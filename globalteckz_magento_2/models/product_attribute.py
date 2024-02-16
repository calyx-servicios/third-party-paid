# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    attribute_magento_id = fields.Integer('Magento Attribute ID')
    attribute_set_magento_id = fields.Many2one('gt.product.attribute.set',string='Magento Attribute Set')
    is_attribute_magento = fields.Boolean('Imported by Magento', default=False)
    