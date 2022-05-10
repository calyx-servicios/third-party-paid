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


from odoo import fields,models, api, _
import requests
import json
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    gt_shopify_order = fields.Boolean(string='Shopify Order',readonly=True)
    gt_shopify_shipped = fields.Boolean(string='Shipped',readonly=True)
    gt_shopify_order_id = fields.Char(string='Order ID',readonly=True)
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_shopify_order_confirmed = fields.Boolean(string='Order Confirmed',readonly=True)
    gt_shopify_order_status_url = fields.Char(string='Order Status URL',readonly=True)
    gt_shopify_order_cancel_reason = fields.Text(string='Cancel Reason')
    gt_shopify_order_currency = fields.Char(string='Order Currency', readonly=True)
    gt_shopify_tax_included = fields.Boolean(string='Tax Included', readonly=True)
    gt_shopify_close_order = fields.Boolean(string='Order Closed')
    gt_financial_status = fields.Char(string="Financial Status",readonly=True)
    gt_fulfillment_status = fields.Char(string="Fillment Status")
    gt_shopify_deliverd = fields.Boolean(string='Order Shipped')
    gt_shopify_invoiced = fields.Boolean(string='Order Invoiced')
    gt_shopify_order_exported =fields.Boolean(string='Shopify Order Exported',readonly=1)
    gt_shopify_order_to_be_exported = fields.Boolean(string='Shopify To be Exported')
    
    
    def gt_close_shopify_order(self):
        return True
        
        
    
    def gt_reopen_shopify_order(self):
        return True
    
    
    
    def gt_shopify_export_order(self):
        if not self.gt_shopify_instance_id:
            raise UserError(_('Please Select Shopify Instance from shopify details'))
        if not self.order_line:
            raise UserError(_('Please Select Products in Order Line'))
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        orders_line = []
        for line in self.order_line:
            if line.product_id.type != 'service':
                if not line.product_id.gt_product_id:
                    raise UserError(_('Please Select Shopify Products Only'))
                taxes = []
                for tax_line in line.tax_id:
                    tax_line= {
                        "price": tax_line.amount * line.product_uom_qty * line.price_unit / 100,
                        "rate": tax_line.amount,
                        "title": str(tax_line.name),
                    }
                    taxes.append(tax_line)
                line_order = {
                    "variant_id": line.product_id.gt_product_id,
                    "quantity": int(round(line.product_uom_qty)),
                    "price": float(line.price_unit),
                    "tax_lines": taxes,
                }
                orders_line.append(line_order)
        if self.partner_id.gt_customer_id:
            vals = {
                "order": {
                  "line_items": orders_line,
                  "customer": {
                    "id": str(self.partner_id.gt_customer_id)
                  },
                  "financial_status": "pending"
                }
              }
        else:
            if not self.partner_id.email:
                raise UserError(_('Please enter Email for the customer'))
            vals = {
                "order": {
                "line_items": orders_line,
                "financial_status": "pending",
                "customer": {
                    "first_name": str(self.partner_id.name),
                    "last_name": "",
                    "email": str(self.partner_id.email),
                  },
                "billing_address": {
                    "first_name": str(self.partner_invoice_id.name),
                    "last_name": "",
                    "address1": str(self.partner_invoice_id.street),
                    "phone": str(self.partner_invoice_id.phone),
                    "city": str(self.partner_invoice_id.city),
                    "province": str(self.partner_invoice_id.state_id.name),
                    "country": str(self.partner_invoice_id.country_id.name),
                    "zip": str(self.partner_invoice_id.name)
                  },
                "shipping_address": {
                    "first_name": str(self.partner_shipping_id.name),
                    "last_name": "",
                    "address1": str(self.partner_shipping_id.street),
                    "phone": str(self.partner_shipping_id.phone),
                    "city": str(self.partner_shipping_id.city),
                    "province": str(self.partner_shipping_id.state_id.name),
                    "country": str(self.partner_shipping_id.country_id.name),
                    "zip": str(self.partner_shipping_id.name)
                  },
                }
              }
        payload=str(vals)
        payload=payload.replace("'",'"')
        payload=str(payload)
        shop_url = shopify_url + 'admin/orders.json'
        response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json'})
        print ("response++++++++++",response)
        print ("json.loads(response.text)+++++++++",json.loads(response.text))
        order_rs=json.loads(response.text)  
        orders = order_rs['order']
        customer = orders['customer']
        if not self.partner_id.gt_customer_id:
            self.partner_id.write({'gt_customer_id':customer['id'],
                'gt_shopify_instance_id':self.gt_shopify_instance_id.id, 'gt_shopify_customer':True,
                'gt_verified_email':customer['verified_email'],})
        self.write({'gt_shopify_order_exported':True,'gt_shopify_order_id':orders['id'],'gt_shopify_order':True,
                    'gt_shopify_order_confirmed':orders['confirmed'],'gt_shopify_order_status_url': orders['order_status_url'],
                    'gt_shopify_order_currency': orders['currency'],'gt_financial_status': orders['financial_status'],
                    })
        return True
        
    
    
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        if self.gt_shopify_order == True:
                order_date = self.date_order
        else:
            order_date = fields.Datetime.now()
        self.write({
            'state': 'sale',
            'confirmation_date': order_date
        })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True
    
 
 
 
 
 
 
 
 
 
    