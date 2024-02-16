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

class GtProductAttributeSet(models.Model):
    _name = "gt.product.attribute.set"
    _description = 'Attribute Set'
 
    name = fields.Char(string='Attribute Set Name',size=64,required=True)
    code= fields.Integer(string='Code',size=100,required=True)
    sort_order = fields.Integer(string='sort Order')
    entity_type_id=fields.Integer(string='Entity Type')
    magento_instance_id = fields.Many2one('gt.magento.instance',string='Magento Instance') 
    attribute_ids=fields.Many2many('gt.product.attributes','attributes','att_id','attribute_id','Attributes')
    attributes_import = fields.Boolean(string='Attributes Import')
