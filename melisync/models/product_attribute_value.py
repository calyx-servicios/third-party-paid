# -*- coding: utf-8 -*-
from odoo import models, fields, _, api

import logging
logger = logging.getLogger(__name__)

class ProductAttributeValueModel(models.Model):
    _inherit = 'product.attribute.value'
    
    meli_id = fields.Char(required=False, string=_('MercadoLibre Attribute Value ID'))
    
    @api.depends('meli_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.meli_id:
                name = '[{}] {}'.format(rec.meli_id, rec.name)
            else:
                name = rec.name
            result.append((rec.id, name))
        return result
