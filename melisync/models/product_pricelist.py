# -*- coding: utf-8 -*-
from odoo import models, _, fields
from datetime import datetime

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    meli_list = fields.Boolean(default=False, string=('Is MercadoLibre list?'), help=_('Show in MercadoLibre pricelists list.'))