# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_brand_id = fields.Many2one(
        'product.brand',
        related='product_template_id.product_brand_id',
        string='Brand'
    )


