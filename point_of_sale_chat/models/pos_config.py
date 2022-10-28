# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Kinfinity Tech Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class POSConfig(models.Model):
    _inherit = 'pos.config'

    enable_pos_chat = fields.Boolean(string="Enable POS Chat")
