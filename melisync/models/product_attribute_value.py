# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.osv import expression

import logging
logger = logging.getLogger(__name__)

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'
    
    meli_id = fields.Char(required=False, string=_('MercadoLibre Attribute Value ID'))
    
    # Nested attributes
    parent_id = fields.Many2one(required=False, comodel_name='product.attribute.value', string=_('Parent ID'))
    child_ids = fields.One2many(comodel_name='product.attribute.value', string=_('Children IDs'), inverse_name='parent_id')
    
    @api.depends('meli_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            name = '[{}] {}'.format(rec.attribute_id.name, rec.name)
            if rec.meli_id:
                name = '%s (Meli ID: %s)'%(name, rec.meli_id)
            result.append((rec.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        domain = expression.OR([
            [['name', operator, name]],
            expression.OR([
                [['meli_id', operator, name]],
                [['attribute_id.name', operator, name]],
            ])
        ])
        ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return [[x.id, x.display_name] for x in self.search([('id', 'in', ids)])]
