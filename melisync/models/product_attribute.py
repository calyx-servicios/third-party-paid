# -*- coding: utf-8 -*-
from odoo import models, fields, _, api

import logging
logger = logging.getLogger(__name__)

class ProductAttributeModel(models.Model):
    _inherit = 'product.attribute'

    meli_id = fields.Char(unique=True, required=False, string=_('MercadoLibre Attribute ID'))
    tag_ids = fields.Many2many(comodel_name='melisync.product.attribute.tags', string=_('Tag IDs'))
    is_required = fields.Boolean(default=lambda self: bool(self.tag_ids.search([('name', 'in', ['required', 'catalog_required']), ('id', 'in', self.tag_ids.ids)])), store=False, readonly=True, string=_('Is required'))

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