# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class PosPromotionType(models.Model):

    _name = 'pos.promotion.type'
    _order = 'sequence'

    name = fields.Char('Name')
    group = fields.Char('Group')
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence')
