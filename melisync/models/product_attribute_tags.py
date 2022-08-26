# -*- coding: utf-8 -*-
from odoo import models, fields, _

class ProductAttributesTags(models.Model):
    _name = 'melisync.product.attribute.tags'
    _description = 'MercadoLibreSync Products Attributes Tags Model'
    _rec_name = 'name'
    
    # Fields
    name = fields.Char(unique=True, required=True, string=_('Name'))
    value = fields.Boolean(required=True, string=_('Value'))