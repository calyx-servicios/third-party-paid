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


class SaleOrder(models.Model):
    _inherit='sale.order'
    
    mage_order_id = fields.Char(string='Order ID', size=100)
    order_status = fields.Char(string='Order Status')
    magento_shop_id = fields.Many2one('gt.magento.store',string='Shop')
    shipped = fields.Boolean('Shipped')
    magento_order = fields.Boolean('Magento Order')
    invoiced = fields.Boolean('Invoiced')
    order_date = fields.Boolean('Magento Order Date')
    entity_id = fields.Char('Entity Id')
    ma_order_id = fields.Char('Magento Order ID')
    payment_method = fields.Many2one('payment.method.magento', 'Payment Method')


class SaleOrderLine(models.Model):
    _inherit='sale.order.line'
    
    entity_id = fields.Float('Entity Id')
    order_item_id = fields.Char('Order Item Id')