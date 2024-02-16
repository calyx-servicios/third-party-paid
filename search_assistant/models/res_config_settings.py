# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Test Case For Bloopark by Agustin Wisky <agustinwisky@gmail.com>

from ast import literal_eval

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_default_partner_id = fields.Many2one('res.partner',string='Sale Default Partner',)
    purchase_default_partner_id = fields.Many2one('res.partner',string='Purchase Default Partner',)

    @api.model
    def get_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).get_values()
        sale_default_partner_id = literal_eval(ICPSudo.get_param('search_assistant.sale_default_partner_id', default='False'))
        purchase_default_partner_id = literal_eval(ICPSudo.get_param('search_assistant.purchase_default_partner_id', default='False'))
        res.update(
            sale_default_partner_id=sale_default_partner_id,
            purchase_default_partner_id=purchase_default_partner_id
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("search_assistant.sale_default_partner_id", self.sale_default_partner_id.id)
        ICPSudo.set_param("search_assistant.purchase_default_partner_id", self.purchase_default_partner_id.id)
        