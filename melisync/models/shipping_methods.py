# -*- coding: utf-8 -*-
from odoo import models, fields, _, api

import logging
logger = logging.getLogger(__name__)

class ShippingModesModel(models.Model):
    _name = 'melisync.shipping.methods'
    _description = 'MercadoLibreSync Shipping Methods Model'
    _rec_name = 'short_name'
    
    # Fields
    method_id = fields.Integer(required=True, string=_('Method ID'))
    name = fields.Char(required=True, string=_('Name'))
    site_id = fields.Many2one(required=True, comodel_name='melisync.site.ids', string=_('Site ID'))
    shipping_modes = fields.Many2many(comodel_name='melisync.shipping.modes', string=_('Shipping Modes'))
    shipping_methods_options_free = fields.Many2many(comodel_name='melisync.shipping.methods.options', string=_('Free modes'))
    delivery_type = fields.Char(required=True, string=_('Delivery type'))
    deliver_to = fields.Char(string=_('Deliver to'))
    min_time = fields.Integer(default=0, string=_('Min time'))
    max_time = fields.Integer(default=0, string=_('Max time'))
    currency_id = fields.Many2one(required=True, comodel_name='res.currency', string=_('Currency ID'))
    company_id = fields.Char(string=_('Company ID'))
    company_name = fields.Char(string=_('Company Name'))

    _sql_constraints = [
        ('method_id_unique', 'unique (method_id, site_id)', 'method_id must be unique for site_id.')
    ]

    # Computed methods
    def _compute_short_name(self):
        for rec in self:
            text = '[{}] {} ({})'.format(rec.deliver_to, rec.name, rec.delivery_type)
            if rec.company_name:
                text = '[{} - {}] {} ({})'.format(rec.company_name, rec.deliver_to, rec.name, rec.delivery_type)
            rec.short_name = text


    # Computed fields
    short_name = fields.Char(compute=_compute_short_name, string=_('Short name'), store=False)

    @api.depends('short_name')
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.short_name))
        return result

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Add search order by context.
        """
        ctx = self._context
        if 'order_display' in ctx:
            order = ctx['order_display']
        return super(ShippingModesModel, self).search(args, offset=offset, limit=limit, order=order, count=count)
    
    @api.model
    def download(self, site_id):
        """
        [{
            "id":73328,
            "name":"Normal a domicilio",
            "type":"standard",
            "deliver_to":"address",
            "status":"active",
            "site_id":"MLA",
            "free_options":[
                "country"
            ],
            "shipping_modes":[
                "me2"
            ],
            "company_id":17500240,
            "company_name":"OCA",
            "min_time":72,
            "max_time":null,
            "currency_id":"ARS"
            }]
        """
        # Objects
        melisync_settings_obj = self.env['melisync.settings']
        melisync_shipping_modes_obj = self.env['melisync.shipping.modes']
        melisync_shipping_methods_options_obj = self.env['melisync.shipping.methods.options']
        res_currency_obj = self.env['res.currency']
        try:
            # Get MercadoLibre client instance
            client = melisync_settings_obj.get_client_instance_blank()
            # Get shipping methods for site_id
            shipping_methods = client.get_shipping_methods(site_id.site_id)
            logger.info('Downloaded {} shipping methods for site {}.'.format(len(shipping_methods), site_id.site_id))
            # Loop shipping methods
            for index, value in enumerate(shipping_methods):
                # Check is method id exists.
                method_id = self.search([('method_id', '=', value.get('id')), ('site_id', '=', site_id.id)])
                # Process shipping modes and free options
                shipping_modes = value.get('shipping_modes', []) or [] # Get shipping modes
                free_options = value.get('free_options', []) or [] # Get free options
                shipping_modes_ids = [] # Save shipping_modes ids
                free_options_ids = [] # Save free_options ids
                # Loop shipping modes for method
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
                        # Append mode_id
                        shipping_modes_ids.append(mode_id.id)
                    except Exception as e:
                        logger.warning(_('Error on create shipping mode "{}": {}').format(mode, e))
                # Loop shipping option for method
                for option in free_options:
                    try:
                        # Check if option exists.
                        option_id = melisync_shipping_methods_options_obj.search([('name', '=', option)])
                        # If option not exists.
                        if not option_id:
                            # Create
                            option_id = melisync_shipping_methods_options_obj.create({
                                'name': option,
                            })
                        # Append option_id
                        free_options_ids.append(option_id.id)
                    except Exception as e:
                        logger.warning(_('Error on create shipping option "{}": {}').format(option, e))
                # If method not exists
                if not method_id:
                    try:
                        # Parse method data
                        method_data = {
                            'method_id': value.get('id'),
                            'name': value.get('name', ''),
                            'site_id': site_id.id,
                            'delivery_type': value.get('type', ''),
                            'deliver_to': value.get('deliver_to', ''),
                            'min_time': value.get('min_time', 0),
                            'max_time': value.get('max_time', 0),
                            'company_id': value.get('company_id', False),
                            'company_name': value.get('company_name', False),
                            'shipping_modes': [(6, False, shipping_modes_ids)],
                            'shipping_methods_options_free': [(6, False, free_options_ids)],
                        }
                        # Get currency_id
                        currency_id = res_currency_obj.search([('name', '=', value.get('currency_id'))])
                        # If currency_id exists.
                        if currency_id:
                            method_data['currency_id'] = currency_id.id
                        # Create method ID
                        self.create(method_data)
                    except Exception as e:
                        logger.warning(_('Error on create method "{}": {}').format(value.get('name'), e))
                else:
                    # Update shipping modes and methods free options for this method
                    try:
                        method_id.write({
                            'shipping_modes': [(6, False, shipping_modes_ids)],
                            'shipping_methods_options_free': [(6, False, free_options_ids)],
                        })
                    except Exception as e:
                        logger.warning(_('Error on update method "{}": {}').format(value.get('name'), e))
        except Exception as e:
            logger.error(_('Error on get shipping methods: {}').format(e))