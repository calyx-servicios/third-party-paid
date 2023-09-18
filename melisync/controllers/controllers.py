# -*- coding: utf-8 -*-
from odoo import http
from werkzeug.utils import redirect
import uuid

import logging
logger = logging.getLogger(__name__)

class Melisync(http.Controller):

    @http.route('/melisync/authorization_url', auth='user')
    def authorization_url(self, **kw):
        """
            Get authorization code after MercadoLibre Authentication
        """
        # Check permissions
        user_rec = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)])
        if not user_rec.has_group('melisync.res_groups_administrator'):
            return "You don't have necessary permissions."
        # Objects
        melisync_settings_obj = http.request.env['melisync.settings']
        # Get site ID
        instance_id = kw.get('instance_id', False)
        if not instance_id:
            return "All parameters are not sended."
        # Get settings instance
        instance = melisync_settings_obj.search([('id', '=', instance_id)])
        if not instance:
            return "Parameters are not valid."
        # Generate state uuid
        state_uuid = uuid.uuid4()
        # Get settings with not check refresh token
        client = instance.get_client_instance(authenticate=False)
        # Generate hash
        hash_code = '{}-{}'.format(instance_id, state_uuid)
        # Get authorization URL.
        url = client.get_authorization_url(hash_code)
        # Save state_uuid.
        instance.write({ 'state_uuid': hash_code })
        # Redirect to login with Meli
        return redirect(url)

    @http.route('/melisync/get_refresh_token', auth='user')
    def get_refresh_token(self, **kw):
        """
            We get the authorization code and get the access Token.
        """
        # Objects
        melisync_settings_obj = http.request.env['melisync.settings']
        melisync_shipping_modes_obj = http.request.env['melisync.shipping.modes']
        melisync_shipping_methods_obj = http.request.env['melisync.shipping.methods']
        ir_model_data_obj = http.request.env['ir.model.data']

        # Check permissions
        user_rec = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)])
        if not user_rec.has_group('melisync.res_groups_administrator'):
            return "You don't have necessary permissions."

        # Save available shipping modes
        available_shipping_modes = []

        # Get state received
        state_uuid = kw.get('state')
        # Get settings with not check refresh token
        instance = melisync_settings_obj.search([('state_uuid', '=', state_uuid)])

        # Compare state_uuid with state received
        if not instance:
            return "Code invalid."

        # Instance Meli library
        client = instance.get_client_instance(authenticate=False)
        try:
            # With authorization code in hands, now, we get the refresh_token.
            data = client.get_refresh_token(kw.get('code'))
        except Exception as e:
            return "Error getting token: {}".format(e)

        # Get user data
        try:
            user_data = client.me()
        except Exception as e:
            return "Error getting user data: {}".format(e)
        
        # Get shipping modes
        try:
            shipping_modes = user_data.get('shipping_modes', [])
            # Loop modes and create if not exists
            for mode in shipping_modes:
                try:
                    # Check if mode exists.
                    mode_id = melisync_shipping_modes_obj.search([('name', '=', mode)])
                    # If mode not exists.
                    if not mode_id:
                        # Create
                        mode_id = melisync_shipping_modes_obj.create({
                            'name': mode,
                        })
                    # Append to list
                    available_shipping_modes.append(mode_id.id)
                except Exception as e:
                    logger.warning('Error on get shipping modes for user: {}'.format(e))
        except Exception as e:
            return "Error on get shipping modes: {}".format(e)

        # Save instance data
        try:
            instance_data_update = {
                'refresh_token': data.get('refresh_token'),
                'user_id': data.get('user_id'),
                'state_uuid': False,
                'shipping_modes': [(6, False, available_shipping_modes)]
            }
            # Get first shipping_mode
            if available_shipping_modes:
                # Get first shipping mode
                instance_data_update['default_shipping_mode'] = available_shipping_modes[0]
                
                # Get shipping methods for shipping mode
                shipping_methods = melisync_shipping_methods_obj.search([('shipping_modes', 'in', [instance_data_update['default_shipping_mode']]), ('site_id', '=', instance.site_id.id)])
                # If shipping mode has shipping methods
                if shipping_methods:
                    instance_data_update['default_shipping_method_free'] = shipping_methods[0].id
                
            # Save data
            instance.write(instance_data_update)
        except Exception as e:
            return "Error saving instance data: {}".format(e)

        # Get the menu data ID.
        menu_id = ir_model_data_obj.search([('module', '=', 'melisync'), ('name', '=', 'menu_root')]).res_id
        # Get the settings action form.
        action = ir_model_data_obj.search([('module', '=', 'melisync'), ('name', '=', 'settings_act_window')]).res_id
        # Parse url to redirect after save refresh token.
        url = '/web#action={action}&cids={id}&id={id}&menu_id={menu_id}&model=melisync.settings&view_type=form'.format(
            id=instance.id,
            action=action,
            menu_id=menu_id,
        )
        return redirect(url)