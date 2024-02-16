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


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    
    
    gt_shopify_active = fields.Boolean(string='Shopify Active')
    gt_shopify_carrier_service_type = fields.Char(string='Shopify Carrier Service Type')
    gt_shopify_carrier_id = fields.Char(string='Shopify Carrier ID')
    gt_shopify_service_discovery = fields.Boolean(string='Shopify Service Discovery')
    gt_shopify_carrier = fields.Boolean(string='Shopify Carrier')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_shopify_code = fields.Char(string='Sopify Carrier Code')

