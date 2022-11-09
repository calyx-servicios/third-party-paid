# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError

import logging
logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    _BUYING_MODE = [
        ('buy_it_now', _('Buy it now')),
        ('auction', _('Auction')),
    ]

    _ITEM_CONDTIONS = [
        ('new', _('New')),
        ('not_specified', ('Not specified')),
        ('used', _('Used')),
    ]

    # Fields
    meli_instance = fields.Many2one(comodel_name='melisync.settings', string=_('Instance'))
    meli_category = fields.Many2one(comodel_name='melisync.categories', string=_('Category'))
    meli_local_pickup = fields.Boolean(default=False, string=_('Local pickup'))
    meli_buying_mode = fields.Selection(required=True, selection=_BUYING_MODE, default='buy_it_now', string=_('Buying mode'))
    meli_condition = fields.Selection(required=True, selection=_ITEM_CONDTIONS, default='new', string=_('Item condition'))
    meli_youtube_url = fields.Char(string=_('Youtube video URL'))
    meli_shipping_mode = fields.Many2one(comodel_name='melisync.shipping.modes', string=_('Shipping mode'))
    meli_shipping_methods_free = fields.Many2many(comodel_name='melisync.shipping.methods', string=_('Shipping methods free'))

    meli_publications = fields.One2many(comodel_name='melisync.publications', inverse_name='product_id', string=_('MercadoLibre publications'))
    
    @api.depends('meli_instance')
    def _get_meli_available_qty(self):
        for rec in self:
            value = 0
            # If settings instance.
            if rec.meli_instance:
                try:
                    # Get warehouse stock for product
                    warehouse_qty = self.browse(rec.id).with_context(warehouse=rec.meli_instance.warehouse_id.id).virtual_available
                    value = warehouse_qty
                except Exception as e:
                    logger.warning(_('Error on getting warehouse stock for product_tmp_id "{}": {}').format(self.id, e))
            rec.meli_available_qty = value

    @api.onchange('meli_shipping_mode')
    def _onchange_shipping_mode(self):
        for rec in self:
            rec.meli_shipping_methods_free = False

    @api.onchange('meli_instance')
    def _onchange_meli_instance(self):
        for rec in self:
            rec.meli_get_instance_shipping_info()
            rec._get_meli_available_qty()
            rec.meli_category = False
    
    @api.depends('meli_instance', 'meli_category', 'meli_shipping_mode', 'image_1920')
    def _get_meli_ready(self):
        for rec in self:
            # Check if product is ready for publish
            rec.meli_ready = all([rec.meli_instance != False, rec.meli_category != False, rec.meli_shipping_mode != False, rec.image_1920 != False])

    # Computed fields
    meli_available_qty = fields.Integer(compute=_get_meli_available_qty, string=_('Warehouse available quantity'), help=_('Available qty for product in warehouse selected for setting instance. Value is 1 if the listing_type = free.'), default=0)
    meli_ready = fields.Boolean(default=False, compute=_get_meli_ready, string=_('Ready for publish'), help=_('This product is ready for publish in MercadoLibre.'), store=True)

    # Related fields
    meli_instance_site_id = fields.Many2one(related='meli_instance.site_id', comodel_name='melisync.site.ids', string=_('Instance Site ID'))
    meli_warehouse_id = fields.Many2one(related='meli_instance.warehouse_id', comodel_name='stock.warehouse', string=_('Instance Warehouse ID'))
    meli_available_shipping_modes = fields.Many2many(related='meli_instance.shipping_modes', comodel_name='melisync.shipping.modes', string=_('Available shipping modes'))
    meli_pricelists = fields.Many2many(related='meli_instance.pricelists', comodel_name='product.pricelist', string=_('Instance Available pricelists'))
    meli_category_attribute_ids = fields.Many2many(related='meli_category.attribute_ids', comodel_name='product.attribute', string=_('Category attributes availables'))

    def write(self, values):
        """
            Override write function
        """
        melisync_publications_obj = self.env['melisync.publications']
        # If published on MercadoLibre
        res = super(ProductTemplate, self).write(values)
        # If already published products on MercadoLibre
        if len(self.meli_publications):
            # Set fields to update automatically when change values.
            listen_fields = [
                'meli_condition',
                'meli_youtube_url',
                'meli_shipping_mode',
                'meli_shipping_methods_free',
                'meli_buying_mode',
                'sale_ok',
                'description_sale',
            ]
            # Fields modified
            modified_fields = [key for key, _ in values.items() if key in listen_fields]
            # If one key of list has modified
            if modified_fields:
                # If disabled sale
                domain = [
                    ('id', 'in', self.meli_publications.ids),
                    ('status', 'in', ['active', 'paused']),
                ]
                # Get publication IDS
                publication_ids = melisync_publications_obj.search(domain)
                # Objects
                client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
                # Loop publications
                for publication in publication_ids:
                    try:
                        # Update publication in MercadoLibre
                        publication.sync(client)
                    except Exception as e:
                        logger.error(_('Error on update product publication "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        return res

    def meli_get_instance_shipping_info(self):
        """
            Update shipping info by setting instance config
        """
        try:
            self.meli_shipping_mode = self.meli_instance.default_shipping_mode
            self.meli_shipping_methods_free = self.meli_instance.default_shipping_methods_free
        except Exception as e:
            raise UserError(_('Error on update fields by setting instance: {}').format(e))

    def meli_button_predict_category(self):
        # Objects
        client = self.meli_instance.get_client_instance(authenticate=False) # Get MercadoLibre instance
        self.meli_predict_category(client)

    # Methods
    def meli_button_category_sync_attributes(self):
        self.meli_category_sync_attributes()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_predict_category(self, client):
        """
            MercadoLibre predict category for this product.
        """
        # Objects
        melisync_categories_obj = self.env['melisync.categories']
        try:
            # Get category predictions for product
            predictions = client.category_predictor(self.meli_instance.site_id.site_id, self.name, limit=1)
            # If predictions
            if not predictions:
                raise Exception(_('no predictions found.'))
            # Get first prediction
            categ_prediction = predictions[0]
            category_id = categ_prediction.get('category_id')
            # Check if category exists
            categ_id = melisync_categories_obj.search([('categ_id', '=', category_id)])
            # If category not exists:
            if not categ_id:
                raise Exception(_('the "{}" category does not exist, please synchronize the categories of your instance.').format(category_id))
            try:
                # Sync attributes.
                categ_id.sync_attributes()
            except Exception as e:
                raise Exception(_('error downloading category attributes: {}').format(e))
            self.write({
                'meli_category': categ_id.id,
            })
        except Exception as e:
            raise UserError(_('Error: {error}').format(error=e))

    def meli_category_sync_attributes(self):
        """
            Synchronize category attributes.
        """
        try:
            self.meli_category.sync_attributes()
        except Exception as e:
            raise UserError(_('Error on download category attributes: {}').format(e))

    def meli_button_publish(self):
        self.meli_publish()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_sync(self):
        self.meli_sync()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_reactivate(self):
        self.meli_reactivate()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_pause(self):
        self.meli_pause()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_close(self):
        self.meli_close()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_close_force(self):
        self.meli_close_force()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_publish(self):
        # Object
        melisync_publications_obj = self.env['melisync.publications']
        try:
            # Parse domain
            domain = [
                ('id', 'in', self.meli_publications.ids),
                ('publication_id', '=', False),
                ('status', '=', 'ready_for_publish'),
            ]
            publications = melisync_publications_obj.search(domain)
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Loop publications
            for publication in publications:
                try:
                    publication.publish(client)
                except Exception as e:
                    raise Exception(_('Error on publish product "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on publish publications for product "{}" (id: {}): {}').format(self.name, self.id, e))
        
    def meli_sync(self):
        # Object
        melisync_publications_obj = self.env['melisync.publications']
        try:
            # Parse domain
            domain = [
                ('id', 'in', self.meli_publications.ids),
                ('publication_id', '!=', False),
                ('status', '=', 'active'),
            ]
            publications = melisync_publications_obj.search(domain)
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Loop publications
            for publication in publications:
                try:
                    publication.sync(client)
                except Exception as e:
                    raise Exception(_('Error on sync product "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on sync publications for product "{}" (id: {}): {}').format(self.name, self.id, e))

    def meli_reactivate(self):
        # Object
        melisync_publications_obj = self.env['melisync.publications']
        try:
            # Parse domain
            domain = [
                ('id', 'in', self.meli_publications.ids),
                ('publication_id', '!=', False),
                ('status', '=', 'paused'),
            ]
            publications = melisync_publications_obj.search(domain)
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Loop publications
            for publication in publications:
                try:
                    publication.reactivate(client)
                except Exception as e:
                    raise Exception(_('Error on reactivate product "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on reactivate publications for product "{}" (id: {}): {}').format(self.name, self.id, e))

    def meli_pause(self):
        # Object
        melisync_publications_obj = self.env['melisync.publications']
        try:
            # Parse domain
            domain = [
                ('id', 'in', self.meli_publications.ids),
                ('publication_id', '!=', False),
                ('status', '=', 'active'),
            ]
            publications = melisync_publications_obj.search(domain)
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Loop publications
            for publication in publications:
                try:
                    publication.pause(client)
                except Exception as e:
                    raise Exception(_('Error on pause product "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on pause publications for product "{}" (id: {}): {}').format(self.name, self.id, e))

    def meli_close(self):
        # Object
        melisync_publications_obj = self.env['melisync.publications']
        try:
            # Parse domain
            domain = [
                ('id', 'in', self.meli_publications.ids),
                ('publication_id', '!=', False),
                ('status', 'in', ['active', 'paused']),
            ]
            publications = melisync_publications_obj.search(domain)
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Loop publications
            for publication in publications:
                try:
                    publication.close(client)
                except Exception as e:
                    raise Exception(_('Error on close product "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on close publications for product "{}" (id: {}): {}').format(self.name, self.id, e))

    def meli_close_force(self):
        # Object
        melisync_publications_obj = self.env['melisync.publications']
        try:
            # Parse domain
            domain = [
                ('id', 'in', self.meli_publications.ids),
                ('publication_id', '!=', False),
                ('status', '=', ['active', 'paused']),
            ]
            publications = melisync_publications_obj.search(domain)
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Loop publications
            for publication in publications:
                try:
                    publication.close_force(client)
                except Exception as e:
                    logger.warning(_('Error on force close product "{}" ({}): {}').format(self.name, publication.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on force close publications for product "{}" (id: {}): {}').format(self.name, self.id, e))
