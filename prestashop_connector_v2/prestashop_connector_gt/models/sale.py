# -*- coding: utf-8 -*-
#############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
import socket
from datetime import timedelta, datetime, date, time
import time
#import mx.DateTime as dt
from odoo import netsvc
from odoo.tools.translate import _
import urllib
import base64
from operator import itemgetter
from itertools import groupby
#
import logging
import cgi
#import ast
import odoo.addons.decimal_precision as dp

class sale_order(models.Model):
    _inherit = "sale.order"
    
#     def total_weight(self,cr,uid,ids,arg1,arg2,context=None):
#         res={}
#         for rec in self.browse(cr,uid,ids):
#             total_wght=0.0
#             if rec.order_line:
#                 for line in rec.order_line:
# #                     wght=line.weight
#                     wght=0.0
#                     total_wght=total_wght + wght
#             res[rec.id]=total_wght
#         return res

    shop_id=fields.Many2one('sale.shop','Shop ID')
    order_status = fields.Many2one('presta.order.status', string="Status")
    presta_order_ref=fields.Char('Order Reference')
    pretsa_payment_mode=fields.Selection([('bankwire','Bankwire'),('cheque','Payment By Cheque'),('banktran','Bank transfer'),('cod','Cash on delivery  (COD)')],string='Payment mode',default='cheque')
    carrier_prestashop=fields.Many2one('delivery.carrier',string='Carrier In Prestashop')
    workflow_order_id=fields.Many2one('import.order.workflow',string='Order Work Flow')
    prestashop_order=fields.Boolean('Prestashop Order')
    message_order_ids=fields.One2many('order.message','new_id','Message Info')
    token=fields.Char('Token')
    presta_id =  fields.Char('presta_id')
    shop_ids = fields.Many2many('sale.shop', 'saleorder_shop_rel', 'saleorder_id', 'shop_id', string="Shop")
    write_date = fields.Datetime(string="Write Date")
    to_be_exported = fields.Boolean(string="To be exported?")
    presta_payment_reference = fields.Char('Prestashop Payment Reference')
    
class sale_order_line(models.Model):
    _inherit='sale.order.line'
    
    gift=fields.Boolean('Gift')
    gift_message=fields.Char('Gift Message')
    wrapping_cost=fields.Float('Wrapping Cost')
    presta_id = fields.Char('presta_id')
    presta_line = fields.Boolean('Is Presta line')
    # shop_ids = fields.Many2many('sale.shop', 'orderline_shop_rel', 'line_id', 'shop_id', string="Shop")

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state','order_id.workflow_order_id')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:

            if line.order_id.state in ['sale', 'done']:
                if not line.order_id.workflow_order_id:
                    if line.product_id.invoice_policy == 'order':
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
                else:
                    if line.order_id.workflow_order_id.invoice_policy == 'order':
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    elif line.order_id.workflow_order_id.invoice_policy == 'delivery':
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
    
class prestaOrderStatus(models.Model):
    _name = 'presta.order.status'

    name = fields.Char(string="Status")
    presta_id = fields.Char(string="Presta ID")


    
    
    
    
    
    
    
    
    