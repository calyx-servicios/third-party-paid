# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class PosPromotionTemplate(models.Model):

    _name = 'pos.promotion.template'

    promotion_id = fields.Many2one(
        comodel_name="pos.promotion", string="Promotion")
    promotion_code = fields.Char(related='promotion_id.promotion_code',
                                 string="Promotion Code",
                                 store=True)

    state = fields.Selection(
        related='promotion_id.state', string='State', store=True)
    template_id = fields.Many2one('product.template', 'Template',
                                  domain="[('available_in_pos', '=', True)]",
                                  required=True)
    fixed_price = fields.Float('Fixed Price')
    disc_percentage = fields.Float('Disc. %')
    disc_amount = fields.Float('Disc. Amount')