# -*- coding: utf-8 -*-
from odoo import models, fields, _

class ShippingModes(models.Model):
    _name = 'melisync.shipping.modes'
    _description = 'MercadoLibreSync Shipping Modes Model'
    _rec_name = 'name'
    
    # Fields
    name = fields.Char(unique=True, required=True, string=_('Name'))