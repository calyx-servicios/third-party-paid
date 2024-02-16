# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#    Globalteckz                                                              #
#    Copyright (C) 2013-Today Globalteckz (http://www.globalteckz.com)        #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU Affero General Public License as           #
#    published by the Free Software Foundation, either version 3 of the       #
#    License, or (at your option) any later version.                          #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU Affero General Public License for more details.                      #
#                                                                             #
#    You should have received a copy of the GNU Affero General Public License #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #   
###############################################################################

from odoo import fields,models

class GtProductAttributeOptions(models.Model):
    _name = "gt.product.attribute.options"
    _description = "Options of selected attributes"
    _rec_name = "label"

    
    attribute_name  = fields.Char( related='attribute_id.attribute_code' , type='char', string='Attribute Code',)
    value  = fields.Char('Value', size=200)
    ipcast = fields.Char('Type cast', size=50)
    label = fields.Char('Label', size=100)
    referential_id = fields.Many2one('gt.magento.instance', 'Magento Instance')
    
    attribute_id = fields.Many2one('gt.product.attributes', 'Attribute')
    product_attr_value = fields.Many2one('product.attribute.value', 'Odoo product Attribute Value')
    
    product_id = fields.Many2one('product.template','Product Template')
    product_temp_id=fields.Many2one('product.product','Product')
    