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

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    
    gt_customer_note = fields.Text(string='Shopify Note')
    gt_customer_state = fields.Many2one('gt.shopify.customer.state', string='Shopify Customer state')
    gt_tax_exempt = fields.Boolean(string='Shopify Tax Exempt')
    gt_verified_email = fields.Boolean(string='Shopify Verified Email')
    gt_customer_id = fields.Char(string= 'Customer ID')
    gt_shopify_customer = fields.Boolean(string='Shopify Customer')
    gt_default_name=fields.Char('Shopify Name')
    gt_default_last_name=fields.Char('Shopify Last Name')
    gt_default_street= fields.Char('Shopify Street')
    gt_default_street2= fields.Char('Shopify Street2')
    gt_default_zip=fields.Char('Shopify Zip', size=24)
    gt_default_city= fields.Char('Shopify City')
    gt_default_state_id= fields.Many2one("res.country.state", 'Shopify State', ondelete='restrict')
    gt_default_country_id=fields.Many2one('res.country', 'Shopify Country', ondelete='restrict')
    gt_default_phone=fields.Char('Shopify Ship Phone')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance',readonly=True)
    
    
    
class GtShopifyCustomerState(models.Model):
    _name = 'gt.shopify.customer.state'
    _description = "The Customer State"
    
    
    name = fields.Char(string='Name')