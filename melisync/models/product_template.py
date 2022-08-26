# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError
import base64
import uuid

import logging
logger = logging.getLogger(__name__)

class ProductsModel(models.Model):
    _inherit = 'product.template'

    _STATUS_TYPE = [
        ('unpublished', _('Unpublished')),
        ('paused', _('Paused')),
        ('active', _('Active')),
        ('closed', _('Closed')),
    ]

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
    meli_id = fields.Char(unique=True, string=_('MercadoLibre ID'))
    meli_image_id = fields.Char(unique=True, string=_('Image ID'))
    meli_status = fields.Selection(required=True, selection=_STATUS_TYPE, default='unpublished', string=_('Publish status'))
    meli_instance = fields.Many2one(comodel_name='melisync.settings', string=_('Instance'))
    meli_category = fields.Many2one(comodel_name='melisync.categories', string=_('Category'))
    meli_local_pickup = fields.Boolean(default=False, string=_('Local pickup'))
    meli_buying_mode = fields.Selection(required=True, selection=_BUYING_MODE, default='buy_it_now', string=_('Buying mode'))
    meli_condition = fields.Selection(required=True, selection=_ITEM_CONDTIONS, default='new', string=_('Item condition'))
    meli_youtube_url = fields.Char(string=_('Youtube video URL'))
    meli_shipping_mode = fields.Many2one(comodel_name='melisync.shipping.modes', string=_('Shipping mode'))
    meli_shipping_methods_free = fields.Many2many(comodel_name='melisync.shipping.methods', string=_('Shipping methods free'))
    meli_listing_type = fields.Many2one(comodel_name='melisync.listing.types', string=_('Listing type'))

    # Compute methods
    @api.depends('meli_instance')
    def _get_product_meli_price(self):
        # Objects
        for rec in self:
            price = 0.0
            try:
                if self.meli_instance:
                    # Process meli_pricelist price for product.
                    price = self.browse(rec.id).with_context({ 'pricelist': self.meli_instance.pricelist.id }).price
            except Exception as e:
                logger.warning(_('Error getting MercadoLibre price of product_tmpl id "{}": {}').format(rec.id, e))
            rec.meli_price = price
    
    @api.depends('meli_instance')
    def _get_meli_available_qty(self):
        for rec in self:
            value = 0
            # If settings instance.
            if rec.meli_instance:
                try:
                    # Get warehouse stock for product
                    warehouse_qty = self.browse(rec.id).with_context(warehouse=rec.meli_instance.warehouse_id.id).virtual_available
                    # If listing_type is free
                    if rec.meli_listing_type.listing_id == 'free':
                        # Max is 1 (get minimoum of qty, 1)
                        value = min(1, warehouse_qty)
                    else:
                        # Else, get warehouse qty
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
            rec.meli_listing_type = rec.meli_instance.default_listing_type
            rec.meli_get_instance_shipping_info()
            rec._get_meli_available_qty()
            rec._get_product_meli_price()
            rec.meli_category = False
    
    @api.depends('meli_id', 'meli_instance', 'meli_category', 'meli_shipping_mode')
    def _get_meli_ready(self):
        for rec in self:
            # Check if product is ready for publish
            rec.meli_ready = all([rec.meli_id == False, rec.meli_instance != False, rec.meli_category != False, rec.meli_shipping_mode != False])

    # Computed fields
    meli_price = fields.Float(compute=_get_product_meli_price, string=_('Pricelist price'), help=_('Price based on pricelist of MercadoLibre instance.'))
    meli_available_qty = fields.Integer(compute=_get_meli_available_qty, string=_('Warehouse available quantity'), help=_('Available qty for product in warehouse selected for setting instance. Value is 1 if the listing_type = free.'))
    meli_ready = fields.Boolean(default=False, compute=_get_meli_ready, string=_('Ready for publish'), help=_('This product is ready for publish in MercadoLibre.'), store=True)

    # Related fields
    meli_instance_site_id = fields.Many2one(related='meli_instance.site_id', comodel_name='melisync.site.ids', string=_('Instance Site ID'))
    meli_warehouse_id = fields.Many2one(related='meli_instance.warehouse_id', comodel_name='stock.warehouse', string=_('Instance Warehouse ID'))
    meli_available_shipping_modes = fields.Many2many(related='meli_instance.shipping_modes', comodel_name='melisync.shipping.modes', string=_('Available shipping modes'))
    meli_pricelist = fields.Many2one(related='meli_instance.pricelist', comodel_name='product.pricelist', string=_('Instance Pricelist ID'))
    meli_category_attribute_ids = fields.Many2many(related='meli_category.attribute_ids', comodel_name='product.attribute', string=_('Category attributes availables'))

    def write(self, values):
        """
            Override write function
        """
        # If published on MercadoLibre
        if self.meli_id:
            # Set fields to update automatically when change values.
            listen_fields = [
                'meli_condition',
                'meli_youtube_url',
                'meli_shipping_mode',
                'meli_shipping_methods_free',
                'meli_condition',
                'meli_buying_mode',
                'sale_ok',
            ]
            # Fields modified
            modified_fields = [key for key, _ in values.items() if key in listen_fields]
            # If one key of list has modified
            if modified_fields:
                # Objects
                client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
                # Update in MercadoLibre
                item_data = self.meli_sync(client)
                # Save item data with MELI data (non updatable fields if product have sales)
                values['name'] = item_data.get('title')
                values['meli_buying_mode'] = item_data.get('buying_mode')
                values['meli_youtube_url'] = item_data.get('video_id', False)
        return super(ProductsModel, self).write(values)

    def meli_get_instance_shipping_info(self):
        """
            Update shipping info by setting instance config
        """
        try:
            self.meli_shipping_mode = self.meli_instance.default_shipping_mode
            self.meli_shipping_methods_free = self.meli_instance.default_shipping_methods_free
        except Exception as e:
            raise UserError(_('Error on update fields by setting instance: {}').format(e))

    def clear_meli_data(self):
        """
            Clear MercadoLibre product data
        """
        self.write({
            'meli_id': False,
            'meli_image_id': False,
            'meli_category': False,
            'meli_status': 'unpublished',
        })
    
    def meli_upload_image(self, client):
        """
            Upload image to Mercadolibre.
        """
        # If product has image.
        if not self.image_1920:
            raise Exception(_('This product doesn\'t have image.'))
        # Set files to upload.
        state_uuid = uuid.uuid4()
        filename = '{}-{}.png'.format(self.id, state_uuid) # Set filename
        binary = base64.b64decode(self.image_1920) # Get binary from base64.
        files = {
            'file': (filename, binary),
        }
        # Upload image in MercadoLibre.
        response = client.item_picture_upload(files)
        return response.get('id')
    
    def meli_get_updatable_data(self, client=None):
        """
            Get product updatable data.
        """
        try:
            # Objects
            client = client or self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Get current item data
            item_data = client.item_get(self.meli_id)
            # Get product editable data
            data = {
                'price': self.meli_price,
                'available_quantity': self.meli_available_qty,
                'condition': self.meli_condition,
                'shipping': self.meli_get_shipping_info(),
            }
            # If item have video_id
            if self.meli_youtube_url:
                data['video_id'] = self.meli_youtube_url,
            # If this item already sold
            if item_data.get('sold_quantity') == 0:
                data['title'] = self.name
                data['buying_mode'] = self.meli_buying_mode
        except Exception as e:
            logger.error(_('Error on get MercadoLibre updatable data for item "{}": {}'.format(self.meli_id, e)))
        return data

    def meli_get_shipping_info(self):
        """
            Get Shipping info for product
        """
        shipping_data = {}
        try:
            # Update shipping mode
            free_shipping = len(self.meli_shipping_methods_free.ids) > 0
            shipping_data['mode'] = self.meli_instance.default_shipping_mode.name
            shipping_data['local_pick_up'] = self.meli_local_pickup
            # Free shipping if product have free methods.
            shipping_data['free_shipping'] = free_shipping
            shipping_data['free_methods'] = []
            # Free delivery
            if free_shipping:
                # Loop free options items
                for free_method in self.meli_shipping_methods_free:
                    try:
                        # Add to free methods
                        free_method_obj = {
                            # Shipping method id
                            'id': free_method.method_id,
                        }
                        # If free methods has rules
                        if free_method.shipping_methods_options_free:
                            # Get free option
                            free_option = None
                            # Get free methods options mode
                            for option in free_method.shipping_methods_options_free:
                                try:
                                    # Create free method with rule
                                    free_method_with_rule = {
                                        **free_method_obj,
                                        'rule': {
                                            'free_mode': option.name,
                                            'value': None
                                        }
                                    }
                                    shipping_data['free_methods'].append(free_method_with_rule)
                                except Exception as e:
                                    logger.warning(_('Error processing product "{}" delivery free method "{}" options: {}').format(self.id, free_method.name, e))
                        else:
                            # Else add free method only without rules
                            shipping_data['free_methods'].append(free_method_obj)
                    except Exception as e:
                        logger.warning(_('Error processing delivery free method "{}" for product "{}": {}').format(free_method.name, self.id, e))
        except Exception as e:
            logger.error(_('Error on process shipping info for product "{}": {}').format(self.id, e))
        return shipping_data

    # Methods
    def meli_button_category_sync_attributes(self):
        self.meli_category_sync_attributes()
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_view(self):
        """
            View item on MercadoLibre
        """
        try:
            # Objects
            client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
            # Get current item data
            item_data = client.item_get(self.meli_id)
            return {
                'url': item_data.get('permalink'),
                'type': 'ir.actions.act_url',
                'target': 'blank',
            }
        except Exception as e:
            raise UserError(_('Error on get product data of MercadoLibre: {}').format(e))

    def meli_button_pause(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_pause(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_reactivate(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_reactivate(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_close(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_close(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_delete_force(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_delete_force(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_sync(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_sync(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_sync_stock(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_sync_stock(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_button_predict_category(self):
        # Objects
        client = self.meli_instance.get_client_instance(authenticate=False) # Get MercadoLibre instance
        self.meli_predict_category(client)

    def meli_button_publish(self):
        # Objects
        client = self.meli_instance.get_client_instance() # Get MercadoLibre instance
        self.meli_publish(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def meli_publish(self, client):
        """
            MercadoLibre publish
        """
        # If product not have image.
        try:
            # Create item data object
            data = {
                'site_id': self.meli_instance.site_id.site_id,
                'price': self.meli_price,
                'available_quantity': self.meli_available_qty,
                'category_id': self.meli_category.categ_id,
                'title': _('Item de Prueba - Por favor, NO OFERTAR #{id}').format(id=self.id) if self.meli_instance.testing_mode else self.name,
                'currency_id': self.meli_instance.currency_id.name,
                'condition': self.meli_condition,
                'listing_type_id': self.meli_listing_type.listing_id,
                'buying_mode': self.meli_buying_mode,
                # Pictures
                'pictures': [],
                # Shipping info
                'shipping': self.meli_get_shipping_info(),
                'attributes': [],
            }
            # If have video URL
            if self.meli_youtube_url:
                data['video_id'] = self.meli_youtube_url
            # Description
            if self.description_sale:
                # Product description
                data['description'] = {
                    'plain_text': self.description_sale,
                }
            # Get MELI attributes
            attribute_line_ids = self.attribute_line_ids
            # Get products attributes
            for line in attribute_line_ids:
                try:
                    # Loop only attributes with meli_id
                    if not line.attribute_id.meli_id:
                        continue

                    # Get first value data
                    value_name = False
                    value_id = False
                    for value in line.attribute_id.value_ids:
                        value_name = value.name
                        value_id = value.meli_id
                        break
                    # Parse attribute data.
                    attr_data = {
                        'id': line.attribute_id.meli_id,
                        'value_name': value_name,
                    }
                    # If value has meli_id.
                    if value_id:
                        attr_data['value_id'] = value_id
                    # Save attribute
                    data['attributes'].append(attr_data)
                except Exception as e:
                    logger.error('Error processing attribute "{}" for `product_t`mpl_id "{}": {}'.format(line.meli_attributes.meli_id, self.id, e))
            try:
                # Upload image.
                meli_image_id = self.meli_upload_image(client)
                # Add pictures to product data
                data['pictures'].append({ 'id': meli_image_id })
            except Exception as e:
                raise Exception(_('Error on upload image to MercadoLibre: {}').format(e))
            # Publish product in MercadoLibre
            item = client.item_create(data)
            # Save product data
            self.write({
                'meli_id': item.get('id'),
                'meli_image_id': meli_image_id,
                'meli_status': 'active',
            })
        except Exception as e:
            logger.error('Error on publish product on MercadoLibre: {}'.format(e))
            raise UserError(e)

    def meli_pause(self, client):
        """
            MercadoLibre pause product
        """
        try:
            # Parse new data.
            data = {
                'status': 'paused',
            }
            # Update in MercadoLibre
            client.item_update(self.meli_id, data)
            # Update product data
            self.write({
                'meli_status': 'paused',
            })
        except Exception as e:
            raise UserError(_('Error on update product in MercadoLibre: {}').format(e))

    def meli_reactivate(self, client):
        """
            MercadoLibre reactivate product
        """
        try:
            # Parse new data.
            data = {
                'status': 'active',
            }
            # Update in MercadoLibre
            client.item_update(self.meli_id, data)
            # Update product data
            self.write({
                'meli_status': 'active',
            })
        except Exception as e:
            raise UserError(_('Error on reactivate product in MercadoLibre: {}').format(e))

    def meli_close(self, client):
        """
            MercadoLibre close product
        """
        try:
            # Parse new data.
            data = {
                'status': 'closed',
            }
            # Update in MercadoLibre
            client.item_update(self.meli_id, data)
            # Clear product MercadoLibre data
            self.clear_meli_data()
        except Exception as e:
            raise UserError(_('Error on update product in MercadoLibre: {}').format(e))

    def meli_delete_force(self, client):
        """
            MercadoLibre close product FORCED
        """
        try:
            self.meli_close(client)
        except Exception as e:
            logger.warning(_('Error on close product "{}" ({}) in MercadoLibre: {}').format(self.name, self.id, e))
        # Clear product MercadoLibre data
        self.clear_meli_data()

    def meli_sync(self, client):
        """
            MercadoLibre synchronize product
            Fields available to update:
                - Available_quantity
                - Precio
                - Video
                - Imágenes
                - Descripción
                - Envío

                Update witouth sales:
                - Título
                - Modo de compra
                - Métodos de Pago distintos de Mercado Pago
        """
        item_data = {}
        try:
            # If product allowed to publish
            if self.sale_ok:
                data = self.meli_get_updatable_data()
                # Update item
                item_data = client.item_update(self.meli_id, data)
            else:
                self.meli_close()
        except Exception as e:
            raise UserError(_('Error on update product in MercadoLibre: {}').format(e))
        return item_data

    def meli_sync_stock(self, client):
        """
            MercadoLibre synchronize product stock
        """
        if self.meli_id:
            try:
                data = {
                    'available_quantity': self.meli_available_qty,
                }
                # Update item
                client.item_update(self.meli_id, data)
            except Exception as e:
                raise UserError(_('Error on update product stock for product "{}" in MercadoLibre: {}').format(self.id, e))

    def meli_predict_category(self, client):
        """
            MercadoLibre predict category for this product.
        """
        # Objects
        melisync_categories_obj = self.env['melisync.categories']
        try:
            # Get category predictions for product
            predictions = client.category_predictor(self.meli_instance.site_id.site_id, self.name, limit=1)
            # If categories
            if predictions:
                # Get first prediction
                categ_prediction = predictions[0]
                category_id = categ_prediction.get('category_id')
                # Check if category exists
                categ_id = melisync_categories_obj.search([('categ_id', '=', category_id)])
                # If category not exists:
                if not categ_id:
                    try:
                        # Get data from category
                        categ_id = melisync_categories_obj.create({
                            'site_id': self.meli_instance.site_id.id,
                            'categ_id': category_id,
                            'name': categ_prediction.get('category_name'),
                            #'parent_id': self.id, # TODO: get parent ID.
                        })
                        # Sync attributes.
                        categ_id.sync_attributes()
                    except Exception as e:
                        raise Exception(_('error downloading category or attributes: {}').format(e))
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