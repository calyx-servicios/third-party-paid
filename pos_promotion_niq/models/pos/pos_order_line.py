# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _


class PosOrderLine(models.Model):

    _inherit = 'pos.order.line'

    origin_price = fields.Float('Origin Unit Price')
    promo_disc_percentage = fields.Float('Disc %')
    promo_disc_amount = fields.Float('Disc Amount')
    promo_fixed_price = fields.Float('Fixed Price')
    promo_get_free = fields.Boolean('Free')
    promotion_id = fields.Many2one('pos.promotion', 'Pos Promotion')