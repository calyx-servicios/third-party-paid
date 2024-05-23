# -*- coding: utf-8 -*-
from odoo import models, fields, _

class ResPartner(models.Model):
    _inherit = 'res.partner'


    meli_id = fields.Char(unique=True, string=_('Meli ID'))
    meli_shipping_id = fields.Char(unique=True, string=_('Mercado Libre Shipping ID:'))

