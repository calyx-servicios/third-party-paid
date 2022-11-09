# -*- coding: utf-8 -*-
from odoo import models, _, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    meli_id = fields.Char(string=_('Meli ID'))
    meli_image_id = fields.Char(string=_('Image ID'))
    meli_available_qty = fields.Integer(compute='_get_meli_available_qty', string=_('Warehouse available quantity'), help=_('Available qty for product in warehouse selected for setting instance. Value is 1 if the listing_type = free.'), default=0)
    meli_price = fields.Float(compute='_get_meli_price', string=_('Pricelist price'), help=_('Price based on pricelist selected.'))
    meli_publications = fields.One2many(comodel_name='melisync.publications.variants', inverse_name='variant_id', string=_('MercadoLibre publications variants'))

    @api.depends('product_tmpl_id')
    def _get_meli_available_qty(self):
        for rec in self:
            value = 0
            try:
                # Get warehouse stock for product
                value = rec.browse(rec.id).with_context(**self.env.context).virtual_available
            except Exception as e:
                logger.warning(_('Error on getting warehouse stock for product_variant "{}": {}').format(self.id, e))
            rec.meli_available_qty = value

    # Compute methods
    @api.depends('product_tmpl_id')
    def _get_meli_price(self):
        product_pricelist_obj = self.env['product.pricelist']
        # Objects
        for rec in self:
            price = 0.0
            try:
                pricelist_id = product_pricelist_obj.browse(self.env.context.get('pricelist'))
                price = pricelist_id.get_product_price(rec, 1, None)
            except Exception as e:
                logger.warning(_('Error getting price for variant id "{}" (product tmpl: "{}"): {}').format(rec.id, rec.product_tmpl_id.id, e))
            rec.meli_price = price

    def meli_get_variant_data(self):
        variation_data = {
            'product_id': self.id,
            'attribute_combinations': [],
        }
        value_ids = self.product_template_attribute_value_ids
        # Loop variant attribute value ids
        for value in value_ids:
            # Parse attribute data
            attr_data = {
                'id': value.attribute_id.meli_id,
                'value_name': value.name,
            }
            # If value has self id.
            if value.product_attribute_value_id.meli_id:
                attr_data['value_id'] = value.product_attribute_value_id.meli_id
            # Save attribute
            variation_data['attribute_combinations'].append(attr_data)
        return variation_data
    
    def write(self, values, **kwargs):
        if values.get('active', None) == False:
            self.meli_delete_variant()
        return super(ProductProduct, self).write(values)

    def unlink(self, **kwargs):
        self.meli_delete_variant()
        return super(ProductProduct, self).unlink()

    def meli_delete_variant(self):
        for variant in self.meli_publications:
            try:
                variant_data = variant.publication_id.delete_variant(variant.meli_id)
                variant.unlink()
            except Exception as e:
                logger.error('error on delete variant: {}'.format(e))