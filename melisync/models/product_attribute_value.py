# -*- coding: utf-8 -*-
from odoo import models, fields, _, api

import logging
logger = logging.getLogger(__name__)

class ProductAttributeValueModel(models.Model):
    _inherit = 'product.attribute.value'
    
    meli_id = fields.Char(unique=True, required=False, string=_('MercadoLibre Attribute Value ID'))

    _sql_constraints = [
        ('meli_id_unique', 'unique (meli_id)', 'MercadoLibre ID must be unique.')
    ]
    
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
