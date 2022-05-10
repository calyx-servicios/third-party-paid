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


class GTShopifyStore(models.Model):
    _name='gt.shopify.store'
    _rec_name = 'gt_store_name'
    _description = "The Shopify Store"
    
    
    gt_store_name = fields.Char(string='Shop Name',size=64, required=True)
    gt_store_province = fields.Char(string='Province')
    gt_store_province_code = fields.Char(string='Province Code')
    gt_store_address1 = fields.Char(string='Address 1')
    gt_store_address2 = fields.Char(string='Address 2')
    gt_store_domain = fields.Char(string='Domain')
    gt_store_country_code = fields.Char(string='Country Code')
    gt_store_zipcode = fields.Char(string='Zip Code')
    gt_store_city = fields.Char(string='City')
    gt_store_id = fields.Char(string='Store ID')
    gt_store_currency = fields.Char(string='Currency')
    gt_store_email = fields.Char(string='Email')
    gt_store_weight_unit = fields.Char(string='Weight Unit')
    gt_store_country_name = fields.Char(string='Country Name')
    gt_store_shop_owner = fields.Char(string='Shop Owner')
    gt_store_plan_display_name = fields.Char(string='Store Display Name')
    gt_store_phone = fields.Char(string='Phone')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')