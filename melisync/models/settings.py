# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError

from ..utils.mercadolibreapi import MercadoLibreClient

import logging
logger = logging.getLogger(__name__)

class Settings(models.Model):
    _name = 'melisync.settings'
    _description = 'MercadoLibreSync Settings Model'
    _rec_name = 'name'

    _PICKING_POLICY_OPTIONS = [
        ('direct', _('As soon as possible')),
        ('one', _('When all products are ready'))
    ]

    # Selections
    name = fields.Char(required=True, unique=True, string=_('Name'))
    client_id = fields.Char(required=True, string=_('Client ID'))
    client_secret = fields.Char(required=True, string=_('Client Secret'))
    refresh_token = fields.Char(string=_('Refresh Token'))
    user_id = fields.Char(string=_('User ID'))
    state_uuid = fields.Char(string=_('State uuid'))
    site_id = fields.Many2one(required=True, comodel_name='melisync.site.ids', string=_('Site ID'))
    #testing_mode = fields.Boolean(default=True, string=_('In testing'), help=_('In testing mode, this products are no published with real name.'))
    test_users = fields.Many2many(comodel_name='melisync.test.users', relation='melisync_settings_test_users_rel', column1='setting_id', column2='user_id', string=_('Test users'))
    company_id = fields.Many2one(required=True, comodel_name='res.company', string=_('Company ID'))
    pricelists = fields.Many2many(comodel_name='product.pricelist', string=_('Available pricelists'), help=_('Available pricelists'))
    warehouse_id = fields.Many2one(required=True, comodel_name='stock.warehouse', string=_('Warehouse ID'))
    picking_policy = fields.Selection(required=True, selection=_PICKING_POLICY_OPTIONS, default='one', string=_('Picking Policy'))
    currency_id = fields.Many2one(required=True, comodel_name='res.currency', string=_('Currency ID'))
    multiprocess = fields.Boolean(default=False, string=_('Use multiprocess'), help=_('Using multiprocess, the downloaded information as downloaded in background mode.'))
    multiprocess_qty_process = fields.Integer(default=5, string=_('Quantity of process'), help=_('Quantity of processes uses to download categories.'))
    last_days_orders_get = fields.Integer(required=True, default=1, string=_('Last days orders get'))
    shipping_modes = fields.Many2many(comodel_name='melisync.shipping.modes', string=_('Available shipping modes'))
    default_shipping_mode = fields.Many2one(comodel_name='melisync.shipping.modes', string=_('Default shipping mode'), help=_('Default shipping mode for all products sync.'))
    default_shipping_methods_free = fields.Many2many(comodel_name='melisync.shipping.methods', string=_('Default shipping free methods'), help=_('Default shipping free methods for all products sync.'))
    auto_sync = fields.Boolean(default=True, string=_('Auto synchronize data'), help=_('Upload and download daily updates for products and sales.'))
    sync_categories_attrs = fields.Boolean(default=False, string=_('Synchronize categories attributes'), help=_('On categories synchronization, download attributes'))

    # Constraints
    @api.constrains('multiprocess_qty_process')
    def _check_multiprocess_qty_process(self):
        self.ensure_one()
        if self.multiprocess:
            if self.multiprocess_qty_process > 100 or self.multiprocess_qty_process < 1:
                raise ValidationError(_('Enter field "Quantity of process" value between 1-100.'))

    @api.constrains('last_days_orders_get')
    def _check_last_days_orders_get(self):
        self.ensure_one()
        if self.last_days_orders_get > 100 or self.last_days_orders_get < 1:
            raise ValidationError(_('Enter field "Last days orders get" value between 1-100.'))

    # Onchange functions
    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            rec.warehouse_id = False
            rec.pricelist = False

    @api.onchange('site_id')
    def _onchange_site_id(self):
        # Variables
        for rec in self:
            rec.currency_id = False
            rec.default_shipping_methods_free = False

    def _get_categories_count(self):
        # Objects
        melisync_categories_obj = self.env['melisync.categories']
        for rec in self:
            try:
                rec.categories_count = len(melisync_categories_obj.search([('site_id', '=', rec.site_id.id)]))
            except Exception as e:
                logger.warning(_('Error on get categories_count for setting ID {}: {}').format(rec.id, e))

    def _get_published_count(self):
        # Objects
        melisync_publications_obj = self.env['melisync.publications']
        for rec in self:
            try:
                rec.published_count = len(melisync_publications_obj.search(rec._get_published_domain()))
            except Exception as e:
                logger.warning(_('Error on get published_count for setting ID {}: {}').format(rec.id, e))

    def _get_sales_count(self):
        # Objects
        sale_order_obj = self.env['sale.order']
        for rec in self:
            try:
                rec.sales_count = len(sale_order_obj.search([('meli_instance', '=', rec.id)]))
            except Exception as e:
                logger.warning(_('Error on get _get_sales_count for setting ID {}: {}').format(rec.id, e))

    def _compute_redirect_uri(self):
        # Objects
        ir_config_parameter_obj = self.env['ir.config_parameter']
        # Get base url param.
        web_base_url = ir_config_parameter_obj.sudo().get_param('web.base.url')
        # Get redirect uri
        redirect_uri = ir_config_parameter_obj.sudo().get_param('melisync.redirect_uri')
        text = '{}{}'.format(web_base_url, redirect_uri)
        self.redirect_uri = text
        return text

    # Computed fields
    categories_count = fields.Integer(compute=_get_categories_count, store=False, default=0, string=_('Categories count'))
    sales_count = fields.Integer(compute=_get_sales_count, store=False, default=0, string=_('Sales count'))
    published_count = fields.Integer(compute=_get_published_count, store=False, default=0, string=_('Published products'))
    redirect_uri = fields.Char(compute=_compute_redirect_uri, default=lambda self: self._compute_redirect_uri(), string=_('Redirect URI'), store=False)

    def authenticate(self):
        """
            Go to authorization URL
        """
        return {
            'url': '/melisync/authorization_url?instance_id={}'.format(self.id),
            'type': 'ir.actions.act_url',
            'target': 'self',
        }

    def deauthenticate(self):
        """
            Clear saved refresh_token.
        """
        # Clear token and state data
        for rec in self:
            rec.write({
                'refresh_token': False,
                'user_id': False,
                'state_uuid': False,
                'shipping_modes': False,
                'default_shipping_mode': False,
                'default_shipping_methods_free': False,
            })
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def create_test_user(self):
        """
            Function to create test users.
        """
        try:
            # Objects
            melisync_test_users_obj = self.env['melisync.test.users']
            # Get MercadoLibre client instance
            client = self.get_client_instance()
            # Create test user
            user = client.create_test_user(self.site_id.site_id)
            # Data to create
            data = {
                **user,
                'site_id': self.site_id.id,
                'user_id': self.user_id,
            }
            # Save user in Odoo
            test_user_id = melisync_test_users_obj.create(data)
            # Save test_user in instance.
            self.write({
                'test_users': [(4, test_user_id.id, None)],
            })
            # Reload the view.
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            raise UserError(e)

    def get_client_instance(self, authenticate=True):
        """
            Get MercadoLibre API instance with/without authentication.
            Parameters:
                - authenticate: boolean (get access token for client).
        """
        try:
            client = None
            # If needs authenticate
            if authenticate:
                # Instance Meli library
                client = MercadoLibreClient(self.client_id, self.client_secret, self.redirect_uri)
                # Get access token
                client.get_access_token(self.refresh_token)
            else:
                client = MercadoLibreClient(self.client_id, self.client_secret, self.redirect_uri)
            return client
        except Exception as e:
            raise UserError(_('Error on get setting instance: {}').format(e))
    
    @api.model
    def get_client_instance_blank(self):
        """
            Get MercadoLibre API instance without credentials.
        """
        return MercadoLibreClient('', '', '')

    def button_view_categories(self):
        """
            View categories of settings instance.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Categories'),
            'view_mode': 'tree,form',
            'res_model': 'melisync.categories',
            'domain': [('site_id', '=', self.site_id.id)],
        }

    def _get_published_domain(self):
        domain = [
            ('instance', '=', self.id),
            ('status', 'in', ['active', 'paused']),
            ('publication_id', '!=', False)
        ]
        return domain
    
    def button_view_published(self):
        """
            View published products of settings instance.
        """
        self.ensure_one()
        # Objects
        melisync_publications_obj = self.env['melisync.publications']
        # Products
        publications = melisync_publications_obj.search(self._get_published_domain())
        prod_ids = list(set([x.product_id.id for x in publications]))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Published/paused products'),
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', prod_ids)],
        }

    def button_view_sales(self):
        """
            View sales of settings instance.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale orders'),
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('meli_instance', '=', self.id)],
        }

    def button_sync_sales(self):
        self.sync_sales()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_sync_categories(self):
        self.sync_categories()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_sync_products_all(self):
        self.sync_products_all()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_sync_products_stock(self):
        self.sync_products_stock()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_publish_ready_products(self):
        self.publish_ready_products()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def sync_categories(self):
        """
            Download all categories of site ID.
        """
        # Objects
        melisync_categories_obj = self.env['melisync.categories']
        try:
            # Get all categories with attributes
            melisync_categories_obj.download_categories(settings_instance=self, withAttributes=self.sync_categories_attrs)
        except Exception as e:
            raise UserError(_('Error on get categories of setting instance "{}" (id {}): {}').format(self.name, self.id, e))

    def sync_sales(self):
        """
            Download all sale_orders of site ID.
        """
        # Objects
        sale_order_obj = self.env['sale.order']
        try:
            # Get all categories with attributes
            sale_order_obj.meli_get_sales(settings_instance=self)
        except Exception as e:
            raise UserError(_('Error on get sales of setting instance "{}" (id {}): {}').format(self.name, self.id, e))
    
    def sync_products_all(self):
        """
            Synchronize all products published in MercadoLibre.
        """
        try:
            # Objects
            product_template_obj = self.env['melisync.publications']
            # Get all products published and active
            domain = [
                ('publication_ids', '!=', []),
            ]
            products = product_template_obj.search(domain)
            # If exists products published
            if products:
                # Get MercadoLibre client instance
                client = self.get_client_instance()
                # Loop products
                for product in products:
                    try:
                        product.sync(client)
                    except Exception as e:
                        logger.warning(_('Error on sync product all data of product "{}" ({}): {}').format(product.name, product.id, e))
        except Exception as e:
            logger.error(_('Error on sync products all of setting instance ID {}: {}').format(self.id, e))
            raise UserError(_('Error on sync products all for this site. Please, review your config.'))
    
    def publish_ready_products(self):
        """
            Publish all ready products in MercadoLibre.
        """
        try:
            # Objects
            product_template_obj = self.env['product.template']
            # Get all products published and active
            domain = [
                ('meli_id', '=', False),
                ('meli_ready', '=', True),
            ]
            products = product_template_obj.search(domain)
            # If exists products published
            if products:
                # Get MercadoLibre client instance
                client = self.get_client_instance()
                # Loop products
                for product in products:
                    try:
                        product.publish(client)
                    except Exception as e:
                        logger.warning(_('Error on publish product "{}" ({}): {}').format(product.name, product.id, e))
        except Exception as e:
            logger.error(_('Error on publish products of setting instance ID {}: {}').format(self.id, e))
            raise UserError(_('Error on publish products for this site. Please, review your config.'))

    @api.model
    def _sync_all_sales(self):
        """
            Synchronize all sales.
        """
        try:
            # Instances domain
            domain = [
                ('user_id', '!=', False),
                ('auto_sync', '=', True),
            ]
            # Get all instances
            instances = self.search(domain)
            # Loop instance
            for instance in instances:
                try:
                    # Download sales.
                    instance.sync_sales()
                except Exception as e:
                    logger.warning(_('Error on download sales for instance {}: {}').format(instance.name, e))
        except Exception as e:
            logger.error(_('Error processing setting instances: {}'.format(e)))

    @api.model
    def _sync_products_all(self):
        """
            Synchronize all instances products published in MercadoLibre.
        """
        try:
            # Instances domain
            domain = [
                ('user_id', '!=', False),
                ('auto_sync', '=', True),
            ]
            # Get all instances
            instances = self.search(domain)
            # Loop instance
            for instance in instances:
                try:
                    # Download sales.
                    instance.sync_products_all()
                except Exception as e:
                    logger.warning(_('Error on sync all products for instance {}: {}').format(instance.name, e))
        except Exception as e:
            logger.error(_('Error processing setting instances: {}'.format(e)))

    @api.model
    def sync_products_stock(self):
        """
            Synchronize all instances stock for all products published in MercadoLibre.
        """
        try:
            # Instances domain
            domain = [
                ('user_id', '!=', False),
                ('auto_sync', '=', True),
            ]
            # Get all instances
            instances = self.search(domain)
            # Loop instance
            for instance in instances:
                try:
                    # Download sales.
                    instance.sync_products_stock()
                except Exception as e:
                    logger.warning(_('Error on sync all products stock for instance {}: {}').format(instance.name, e))
        except Exception as e:
            logger.error(_('Error processing setting instances: {}'.format(e)))

    @api.model
    def _publish_ready_products(self):
        """
            Publish all instances ready products in MercadoLibre.
        """
        try:
            # Instances domain
            domain = [
                ('user_id', '!=', False),
                ('auto_sync', '=', True),
            ]
            # Get all instances
            instances = self.search(domain)
            # Loop instance
            for instance in instances:
                try:
                    # Download sales.
                    instance.publish_ready_products()
                except Exception as e:
                    logger.warning(_('Error on publish all ready products for instance {}: {}').format(instance.name, e))
        except Exception as e:
            logger.error(_('Error processing setting instances: {}'.format(e)))