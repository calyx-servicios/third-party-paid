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


class GtProductAttributes(models.Model):
    _name = "gt.product.attributes"
    _description = "Attributes of products"
    _rec_name = "attribute_code"
    
    attribute_code =fields.Char('Code', size=200)
    magento_id  = fields.Char('Magento ID')
    options = fields.One2many('gt.product.attribute.options', 'attribute_id', 'Attribute Options')
    frontend_input_id = fields.Many2one('gt.frontend.input',string='Frontend Input')                                          
    frontend_class = fields.Char('Frontend Class', size=100)
    backend_model = fields.Char('Backend Model', size=200)
    backend_type = fields.Selection([
        ('static', 'Static'),
        ('varchar', 'Varchar'),
        ('text', 'Text'),
        ('decimal', 'Decimal'),
        ('int', 'Integer'),
        ('datetime', 'Datetime')], 'Backend Type')
    scope = fields.Selection([
        ('store', 'Store View'),
        ('website', 'Website'),
        ('global', 'Global')], 'Scope')
    frontend_label = fields.Char('Label', size=100)
    is_visible_in_advanced_search = fields.Boolean('Visible in advanced search?', required=False)
    is_global  = fields.Boolean('Global ?', required=False)
    is_filterable =fields.Boolean('Filterable?', required=False)
    is_comparable = fields.Boolean('Comparable?', required=False)
    is_visible =fields.Boolean('Visible?', required=False)
    is_searchable =fields.Boolean('Searchable ?', required=False)
    is_user_defined = fields.Boolean('User Defined?', required=False)
    is_configurable = fields.Boolean('Configurable?', required=False)
    is_visible_on_front = fields.Boolean('Visible (Front)?', required=False)
    is_used_for_price_rules = fields.Boolean('Used for pricing rules?', required=False)
    is_unique = fields.Boolean('Unique?', required=False)
    is_required = fields.Boolean('Required?', required=False)
    position = fields.Integer('Position', required=False)
    group_id = fields.Integer('Group')
    apply_to = fields.Char('Apply to', size=200)
    default_value = fields.Char('Default Value', size=10)
    note  = fields.Char('Note', size=200)
    entity_type_id = fields.Integer('Entity Type')
    referential_id = fields.Many2one('gt.magento.instance', 'Magento Instance', readonly=True)
        #These parameters are for automatic management
    field_name = fields.Char('Open ERP Field name', size=100)
    attribute_set_info = fields.Text('Attribute Set Information')
    based_on = fields.Selection([('product_product', 'Product Product'), ('product_template', 'Product Template')], 'Based On')

    odoo_attr_id = fields.Many2one('product.attribute', 'Odoo Attribute')
      
      
class GtFrontendInput(models.Model):
    _name = "gt.frontend.input"
    _description = "Frontend Input type"
    _rec_name = "name_type"

    name_type  = fields.Char(string='Name')
    
    
    
    