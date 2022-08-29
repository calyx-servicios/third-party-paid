# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.osv import expression

import logging
logger = logging.getLogger(__name__)

class ProductAttributeModel(models.Model):
    _inherit = 'product.attribute'

    meli_id = fields.Char(unique=True, required=False, string=_('MercadoLibre Attribute ID'))
    tag_ids = fields.Many2many(comodel_name='melisync.product.attribute.tags', string=_('Tag IDs'))
    is_required = fields.Boolean(default=lambda self: bool(self.tag_ids.search([('name', 'in', ['required', 'catalog_required']), ('id', 'in', self.tag_ids.ids)])), store=False, readonly=True, string=_('Is required'))

    _sql_constraints = [
        ('meli_id_unique', 'unique (meli_id)', 'meli_id must be unique.'),
        ('name_unique', 'unique (name)', 'name must be unique.'),
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

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        domain = expression.OR([[['name', operator, name]], [['meli_id', operator, name]]])
        ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return [[x.id, x.display_name] for x in self.search([('id', 'in', ids)])]