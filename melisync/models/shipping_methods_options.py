# -*- coding: utf-8 -*-
from odoo import models, fields, _

class ShippingMethodsOptions(models.Model):
    _name = 'melisync.shipping.methods.options'
    _description = 'MercadoLibreSync Shipping Methods Options Model'
    _rec_name = 'name'
    
    # Fields
    name = fields.Char(unique=True, required=True, string=_('Name'))