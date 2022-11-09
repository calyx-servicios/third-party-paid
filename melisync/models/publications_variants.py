# -*- coding: utf-8 -*-
from odoo import models, _, fields, api
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class PublicationsVariants(models.Model):
    _name = 'melisync.publications.variants'
    _description = 'MercadoLibre Publications Variants Model'

    publication_id = fields.Many2one(required=True, comodel_name='melisync.publications', string=_('Publication'))    
    variant_id = fields.Many2one(required=True, comodel_name='product.product', string=_('Product variant'))    
    meli_id = fields.Char(string=_('Meli ID'))
    meli_image_id = fields.Char(string=_('Image ID'))

class PublicationsVariantsRelations(models.Model):
    _name = 'melisync.publications.variants.relations'
    _description = 'MercadoLibre Publications Variants Relations Model'

    variant_id = fields.Many2one(required=True, comodel_name='product.product', string=_('Product variant'))    
    meli_id = fields.Char(required=True, string=_('Meli ID'))