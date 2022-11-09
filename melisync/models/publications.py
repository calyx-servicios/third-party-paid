# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError
import base64
import uuid

import logging
logger = logging.getLogger(__name__)

class Publications(models.Model):
    _name = 'melisync.publications'
    _description = 'MercadoLibre Publications Model'

    _STATUS_TYPE = [
        ('ready_for_publish', _('Ready for publish')),
        ('paused', _('Paused')),
        ('active', _('Active')),
        ('closed', _('Closed')),
    ]

    product_id = fields.Many2one(required=True, comodel_name='product.template', string=_('Product'))
    listing_type = fields.Many2one(required=True, comodel_name='melisync.listing.types', string=_('Listing type'))
    pricelist = fields.Many2one(required=True, comodel_name='product.pricelist', string=_('Pricelist'))
    price = fields.Float(compute='_get_price', string=_('Pricelist price'), help=_('Price based on pricelist selected.'))
    publication_id = fields.Char(string=_('Publication ID'))
    status = fields.Selection(required=True, selection=_STATUS_TYPE, default='ready_for_publish', string=_('Publish status'))
    available_qty = fields.Integer(compute='_get_available_qty', string=_('Product available quantity'), help=_('Available qty for product in warehouse selected for setting instance. Value is 1 if the listing_type = free.'), default=0)
    image_id = fields.Char(string=_('Image ID'))

    # Related fields
    available_pricelists = fields.Many2many(related='product_id.meli_pricelists', comodel_name='product.pricelist', string=_('Available pricelists'))
    product_available_qty = fields.Integer(related='product_id.meli_available_qty', string=_('Warehouse available quantity'), help=_('Available qty for product in warehouse selected for setting instance. Value is 1 if the listing_type = free.'))
    instance = fields.Many2one(related='product_id.meli_instance', comodel_name='melisync.settings', string=_('Instance'))
    site_id = fields.Many2one(related='instance.site_id', comodel_name='melisync.site.ids', string=_('Site ID'))
    category = fields.Many2one(related='product_id.meli_category', comodel_name='melisync.categories', string=_('Category'))

    local_pickup = fields.Boolean(related='product_id.meli_local_pickup', default=False, string=_('Local pickup'))
    buying_mode = fields.Selection(related='product_id.meli_buying_mode', required=True, string=_('Buying mode'))
    condition = fields.Selection(related='product_id.meli_condition', required=True, string=_('Item condition'))
    youtube_url = fields.Char(related='product_id.meli_youtube_url', string=_('Youtube video URL'))
    shipping_mode = fields.Many2one(related='product_id.meli_shipping_mode', comodel_name='melisync.shipping.modes', string=_('Shipping mode'))
    shipping_methods_free = fields.Many2many(related='product_id.meli_shipping_methods_free', comodel_name='melisync.shipping.methods', string=_('Shipping methods free'))
    attribute_line_ids = fields.One2many(related='product_id.attribute_line_ids', comodel_name='product.template.attribute.line', string=_('Product Attributes'))
    description_sale = fields.Text(related='product_id.description_sale', string=_('Sales Description'))
    
    user_is_meli_administrator = fields.Boolean(default=False, compute='_compute_user_is_meli_administrator', string=_('Is MercadoLibre Administrator?'))

    # Publication variants
    variants = fields.One2many(comodel_name='melisync.publications.variants', inverse_name='publication_id', string=_('Publication variants'))

    # Constraints
    _sql_constraints = [
        ('publication_id_unique', 'unique (publication_id)', 'publication_id must be unique.'),
        ('product_listing_unique', 'unique (product_id, listing_type)', 'product id, listing type must be unique.'),
    ]

    def _compute_user_is_meli_administrator(self):
        for rec in self:
            rec.user_is_meli_administrator = self.env.user.has_group('melisync.res_groups_sales_administrator')

    # Compute methods
    @api.depends('pricelist')
    def _get_price(self):
        # Objects
        for rec in self:
            price = 0.0
            try:
                if rec.pricelist:
                    # Process meli_pricelist price for product.
                    price = rec.pricelist.get_product_price(rec.product_id, 1, None)
            except Exception as e:
                logger.warning(_('Error getting price for publication id "{}" (product tmpl: "{}"): {}').format(rec.id, rec.product_id.id, e))
            rec.price = price

    @api.depends('product_available_qty')
    def _get_available_qty(self):
        for rec in self:
            value = rec.product_available_qty
            try:
                # If listing_type is free
                if rec.listing_type.listing_id == 'free':
                    # Max is 1 (get minimoum of qty, 1)
                    value = min(1, value)
            except Exception as e:
                logger.warning(_('Error on getting warehouse stock for publication id: "{}" (product_tmp_id "{}"): {}').format(rec.id, rec.product_id.id, e))
            rec.available_qty = value

    # Other methods
    @api.depends('product_id', 'listing_type')
    def name_get(self):
        result = []
        for rec in self:
            name = '[{}] {}'.format(rec.listing_type.name, rec.product_id.name)
            result.append((rec.id, name))
        return result

    def button_view(self):
        """
            View item on MercadoLibre
        """
        url = self.get_url()
        return {
            'url': url,
            'type': 'ir.actions.act_url',
            'target': 'blank',
        }

    def button_pause(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.pause(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_reactivate(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.reactivate(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_close(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.close(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_close_force(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.close_force(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_sync(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.sync(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_publish(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.publish(client)
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _check_has_publication_id(self):
        if not self.publication_id:
            raise UserError(_('The publication instance "{}" (product: "{}") has not published in MercadoLibre.').format(self.id, self.product_id.name))

    def clear_meli_data(self):
        """
            Clear MercadoLibre product data
        """
        self.write({
            'status': 'closed',
            #'publication_id': False,
            #'image_id': False,
        })
        # Unlink variants
        if self.variants:
            self.variants.unlink()

    def get_url(self):
        try:
            # Objects
            client = self.instance.get_client_instance() # Get MercadoLibre instance
            # Get current item data
            item_data = client.item_get(self.publication_id)
            return item_data.get('permalink')
        except Exception as e:
            raise UserError(_('Error on get product data of MercadoLibre of publication "{}" (product: "{}"): {}').format(self.publication_id, self.product_id.name, e))
    
    def upload_image(self, client, image):
        """
            Upload image to Mercadolibre.
        """
        # Set files to upload.
        state_uuid = uuid.uuid4()
        filename = '{}.png'.format(state_uuid) # Set filename
        binary = base64.b64decode(image) # Get binary from base64.
        file_data = {
            'file': (filename, binary),
        }
        # Upload image in MercadoLibre.
        response = client.item_picture_upload(file_data)
        return response.get('id')

    def publish(self, client):
        """
            MercadoLibre publish
        """
        # Objects
        product_product_obj = self.env['product.product']
        publications_variants_relations_obj = self.env['melisync.publications.variants.relations']
        
        # Validations
        if self.publication_id:
            raise UserError(_('The publication instance "{}" (product: "{}") has been already published in MercadoLibre.').format(self.id, self.product_id.name))

        if not self.product_id.sale_ok:
            raise UserError(_('The product "{}" is not allowed for sale.').format(self.product_id.name))

        try:
            # Create item data object
            data = {
                'site_id': self.instance.site_id.site_id,
                'category_id': self.category.categ_id,
                'title': _('Item de Prueba - Por favor, NO OFERTAR #{id}').format(id=self.product_id.id) if self.instance.testing_mode else self.product_id.name,
                'currency_id': self.instance.currency_id.name,
                'condition': self.condition,
                'listing_type_id': self.listing_type.listing_id,
                'buying_mode': self.buying_mode,
                # Pictures
                'pictures': [],
                # Shipping info
                'shipping': self.get_shipping_info(),
            }
            # ==========
            # If have video URL
            if self.youtube_url:
                data['video_id'] = self.youtube_url
            # ==========
            # Get MELI attributes
            attrs = self.get_attributes_and_variants()
            # Add attributes to data object
            data = {
                **data,
                **attrs,
            }
            # If product has not variants, add price and available qty.
            if not data.get('variants', []):
                data['price'] = self.price
                data['available_quantity'] = self.available_qty
            # ==========
            try:
                # If product has image.
                if not self.product_id.image_1920:
                    raise Exception(_('the product "{}" (id: {}) doesn\'t have image.').format(self.product_id.name, self.product_id.id))
                # Upload image.
                meli_image_id = self.upload_image(client, self.product_id.image_1920)
                # Add pictures to product data
                data['pictures'].append({ 'id': meli_image_id })
            except Exception as e:
                raise Exception(_('Error on upload image to MercadoLibre: {}').format(e))
            # ==========
            variation_ids_data = []
            try:
                # Add image for variations
                for variation in data.get('variations', []):
                    product_id = variation.pop('product_id') # Get Odoo product ID
                    # Set variation data
                    variation_data = {
                        'product_id': product_id,
                        'image_id': None,
                    }
                    variant_id = product_product_obj.browse(product_id)
                    # Compare variant image with template image
                    if variant_id.image_1920 != self.product_id.image_1920:
                        # Upload variant image.
                        variation_data['image_id'] = self.upload_image(client, variant_id.image_1920)
                    else:
                        variation_data['image_id'] = meli_image_id
                    # Add image ids
                    variation['picture_ids'] = [variation_data['image_id']]
                    variation_ids_data.append(variation_data)
            except Exception as e:
                raise Exception(_('Error on upload variant image to MercadoLibre: {}').format(e))
            # ==========
            # Publish product in MercadoLibre
            item = client.item_create(data)
            # ==========
            # Save product data
            self.write({
                'status': 'active',
                'publication_id': item.get('id'),
                'image_id': meli_image_id,
            })
            # Post description
            if self.description_sale:
                self.update_description(client)
            # Save variations IDS
            for index, variation in enumerate(item.get('variations', [])):
                try:
                    # Get variation data
                    variation_data = variation_ids_data[index]
                    # Save publication variant
                    self.write({
                        'variants': [(0, False, {
                            'variant_id': variation_data.get('product_id'),
                            'meli_id': variation.get('id'),
                            'meli_image_id': variation_data.get('image_id'),
                        })]
                    })
                    # Save relations FOREVER
                    publications_variants_relations_obj.create({
                        'meli_id': variation.get('id'),
                        'variant_id': variation_data.get('product_id'),
                    })
                except Exception as e:
                    raise UserError(_('Error on save product variants ids "{}" ({}) to MercadoLibre:\n\n{}\n\nPlease, add product description updating product in MercadoLibre.').format(self.product_id.name, self.listing_type.name, e))
        except Exception as e:
            raise UserError(_('Error on upload product "{}" ({}) to MercadoLibre:\n\n{}').format(self.product_id.name, self.listing_type.name, e))

    def update_description(self, client):
        """
            Update item description
        """
        try:
            client.item_update_description(self.publication_id, {
                'plain_text': self.description_sale or '',
            })
        except Exception as e:
            raise UserError(_('Error on update product description "{}" ({}) to MercadoLibre:\n\n{}\n\nPlease, add product description updating product in MercadoLibre.').format(self.product_id.name, self.listing_type.name, e))

    def get_attributes_and_variants(self):
        """
            Get product attributes
            Return:

            {
                'attributes': [],
                'variations': [  
                    {  
                        'attribute_combinations': []
                    },
                ],
            }
        """
        data = {
            'attributes': [],
            'variations': [],
        }
        # Parse attributes domain
        attrs_domain = [
            ('id', 'in', self.attribute_line_ids.ids), # Attri
            ('attribute_id.create_variant', '=', 'no_variant'), # If attribute has not create variant
            ('attribute_id.meli_id', '!=', False), # Loop only attributes with meli_id
        ]
        # Get product attributes
        for line in self.attribute_line_ids.search(attrs_domain):
            try:
                # Parse variables
                attr_id = line.attribute_id
                # Parse attribute data
                for value in line.value_ids:
                    attr_data = {
                        'id': attr_id.meli_id,
                        'value_name': value.name,
                    }
                    # If value has self id.
                    if value.meli_id:
                        attr_data['value_id'] = value.meli_id
                    # Save attribute
                    data['attributes'].append(attr_data)
                    break
            except Exception as e:
                raise UserError('Error processing attribute "{}" (product "{}"): {}'.format(attr_id.meli_id, self.product_id.name, e))
        # Loop product variants
        for variant in self.product_id.product_variant_ids:
            variation_data = variant.meli_get_variant_data()
            # Get other product data
            variation_data['available_quantity'] = variant.with_context(warehouse=self.instance.warehouse_id.id).meli_available_qty
            variation_data['price'] = self.price # self.with_context(pricelist=self.pricelist.id).meli_price
            # Save product variation data
            data['variations'].append(variation_data)
        return data

    def pause(self, client):
        """
            MercadoLibre pause product
        """
        self._check_has_publication_id() # Check if product has been published
        try:
            # Parse new data.
            data = {
                'status': 'paused',
            }
            # Update in MercadoLibre
            client.item_update(self.publication_id, data)
            # Update product data
            self.write({
                'status': 'paused',
            })
        except Exception as e:
            raise UserError(_('Error on pause publication "{}" (product "{}") in MercadoLibre: {}').format(self.id, self.product_id.name, e))

    def reactivate(self, client):
        """
            MercadoLibre reactivate product
        """
        self._check_has_publication_id() # Check if product has been published
        try:
            # Parse new data.
            data = {
                'status': 'active',
            }
            # Update in MercadoLibre
            client.item_update(self.publication_id, data)
            # Update product data
            self.write({
                'status': 'active',
            })
        except Exception as e:
            raise UserError(_('Error on reactivate publication "{}" (product "{}") in MercadoLibre: {}').format(self.id, self.product_id.name, e))

    def close(self, client):
        """
            MercadoLibre close product
        """
        self._check_has_publication_id() # Check if product has been published
        try:
            # Parse new data.
            data = {
                'status': 'closed',
            }
            # Update in MercadoLibre
            client.item_update(self.publication_id, data)
            # Clear product MercadoLibre data
            self.clear_meli_data()
        except Exception as e:
            raise UserError(_('Error on close publication "{}" (product "{}") in MercadoLibre: {}').format(self.id, self.product_id.name, e))

    def close_force(self, client):
        """
            MercadoLibre close product FORCED
        """
        try:
            self.close(client)
        except Exception as e:
            logger.warning(_('Error on close publication "{}" (product "{}") in MercadoLibre: {}').format(self.id, self.product_id.name, e))
        # Clear product MercadoLibre data
        self.clear_meli_data()

    def sync(self, client):
        """
            MercadoLibre synchronize product
            Fields available to update:
                - available_quantity
                - price
                - video
                - TODO: images
                - description
                - shipping

                Update witouth sales:
                - title
                - shipping_mode
                - payment methods
        """
        product_product_obj = self.env['product.product']
        publications_variants_obj = self.env['melisync.publications.variants']
        self._check_has_publication_id() # Check if product has been published
        try:
            # If product allowed to publish
            if self.product_id.sale_ok:
                # Update variants
                attrs = self.get_attributes_and_variants()
                added_variations = []
                # Loop existent variations
                for variation in attrs.get('variations', []):
                    try:
                        # Get variation product id
                        product_id = variation.pop('product_id')
                        # Check variant publication
                        current_publication = publications_variants_obj.search([
                            ('publication_id', '=', self.id),
                            ('variant_id', '=', product_id),
                        ], limit=1)

                        # If variation is not published
                        if not current_publication:
                            try:
                                image_id = None
                                # Get product
                                variant_id = product_product_obj.browse(product_id)
                                # Get variation MELI attributes
                                item_data = variant_id.meli_get_variant_data()
                                item_data.pop('product_id')
                                # Get other product data
                                item_data['available_quantity'] = variant_id.with_context(warehouse=self.instance.warehouse_id.id).meli_available_qty
                                item_data['price'] = self.price # self.with_context(pricelist=self.pricelist.id).meli_price
                                # Add image
                                # Compare variant image with template image
                                if variant_id.image_1920 != self.product_id.image_1920:
                                    # Upload variant image.
                                    image_id = self.upload_image(client, variant_id.image_1920)
                                    # Add picture to self item pictures list.
                                    res = client.item_picture_add(self.publication_id, image_id)
                                else:
                                    image_id = self.image_id
                                item_data['picture_ids'] = [image_id]
                                # Create new variation
                                new_variation = client.item_variation_create(self.publication_id, item_data)
                                variation_data = new_variation[-1] # Get first item
                                # Save variation
                                self.write({
                                    'variants': [(0, False, {
                                        'variant_id': product_id,
                                        'meli_id': variation_data.get('id'),
                                        'meli_image_id': image_id,
                                    })],
                                })
                                # Save variation ID
                                added_variations.append(variation_data.get('id'))
                            except Exception as e:
                                raise Exception(_('error on publish variant: {}').format(e))
                    except Exception as e:
                        raise Exception(_('error processing variant: {}'.format(e)))
                # Get product updatable data
                data = self.get_updatable_data()
                # Update only old variations
                data['variations'] = [variant for variant in data.get('variations') if variant.get('id') not in added_variations]
                # ==========
                # Update item
                client.item_update(self.publication_id, data)
                # Update description
                self.update_description(client)
            else:
                self.close_force(client)
        except Exception as e:
            raise UserError(_('Error on update publication for product "{}" in MercadoLibre: {}').format(self.product_id.name, e))

    def get_updatable_data(self, client=None):
        """
            Get product updatable data.
        """
        try:
            # Objects
            client = client or self.instance.get_client_instance() # Get MercadoLibre instance
            # Get current item data
            item_data = client.item_get(self.publication_id)
            # Get product editable data
            data = {
                'condition': self.condition,
                'shipping': self.get_shipping_info(),
            }
            # If item have video_id
            if self.youtube_url:
                data['video_id'] = self.youtube_url
            # If this item already sold
            if item_data.get('sold_quantity') == 0:
                data['title'] = self.product_id.name
                data['buying_mode'] = self.buying_mode
            
            # If product has not variants, add price and stock
            if not self.variants:
                data['price'] = self.price
                data['available_quantity'] = self.available_qty
            else:
                # Get published variations data
                data['variations'] = []
                for publication_variant in self.variants:
                    try:
                        variant_data = {
                            'id': publication_variant.meli_id,
                            'available_quantity': publication_variant.variant_id.with_context(warehouse=self.instance.warehouse_id.id).meli_available_qty,
                            'price': self.price,
                        }
                        data['variations'].append(variant_data)
                    except Exception as e:
                        raise UserError(_('Error parsing variant "{}" data: {}').format(publication_variant.id, e))
        except Exception as e:
            raise UserError(_('Error on get MercadoLibre updatable data for publication id: "{}" (item "{}"): {}'.format(self.id, self.publication_id, e)))
        return data

    def delete_variant(self, variation_id):
        try:
            # Objects
            client = self.instance.get_client_instance() # Get MercadoLibre instance
            return client.item_variation_delete(self.publication_id, variation_id)
        except Exception as e:
            raise UserError(_('Error on delete variation ID "{}" for publication id: "{}" (item "{}"): {}'.format(variation_id, self.id, self.publication_id, e)))

    def get_shipping_info(self):
        """
            Get Shipping info for product
        """
        shipping_data = {}
        try:
            # Update shipping mode
            free_shipping = len(self.shipping_methods_free.ids) > 0
            shipping_data['mode'] = self.instance.default_shipping_mode.name
            shipping_data['local_pick_up'] = self.local_pickup
            # Free shipping if product have free methods.
            shipping_data['free_shipping'] = free_shipping
            shipping_data['free_methods'] = []
            # Free delivery
            if free_shipping:
                # Loop free options items
                for free_method in self.shipping_methods_free:
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
                        raise Exception(_('Error processing delivery free method "{}" for product "{}": {}').format(free_method.name, self.id, e))
        except Exception as e:
            raise UserError(_('Error on process shipping info for product "{}": {}').format(self.id, e))
        return shipping_data

    def unlink(self):
        # Objects
        client = self.instance.get_client_instance() # Get MercadoLibre instance
        self.close_force(client)
        return super(Publications, self).unlink()