# -*- coding: utf-8 -*-
from odoo import models, fields, _

class ResPartnerModel(models.Model):
    _inherit = 'res.partner'

    meli_id = fields.Char(string=_('Meli ID'))
