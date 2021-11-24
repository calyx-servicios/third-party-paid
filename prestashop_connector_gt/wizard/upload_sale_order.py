from odoo import tools
from odoo import api, fields, models
from odoo.tools.translate import _
import io
import base64

class upload_sale_order(models.TransientModel):
    _name="prestashop.upload.orders"
    _description = 'Upload Orders'
              
    prestashop_id=fields.Many2one('prestashop.instance','Prestashop Instance')
    
    # @api.one
    def upload_orders(self,context=None,res_ids=None,presta_id=None):
        sale_order=self.env['sale.order']
        sale_order_line=self.env['sale.order.line']
        account_obj=self.env['account.move']
        picking_obj=self.env['stock.picking']
#         active_ids=self._context.get('active_ids')
        if context==None:
            context=self._context
        else:
            context=context
#         print "srlf",self
        if res_ids and isinstance(res_ids,list):
            rec_list=res_ids
            presta_inst_id=presta_id.id
        else:
            active_ids=context.get('active_ids')
            rec_list=active_ids
            presta_inst_id=self.prestashop_id.id

        for rec in rec_list:
            sale_order_obj=sale_order.browse(rec)
            #get all sale order records from odoo
#             presta_inst_id=self.prestashop_id.id
            prestashop=self.env['sale.shop'].browse(presta_inst_id).presta_connect_json()
            #??
            prestashop.debug = True
            sale_order_get=prestashop.get('orders')
            # get all sale order records from prestashop
            payment_value = dict(self.env['sale.order'].fields_get(allfields=['pretsa_payment_mode'])['pretsa_payment_mode']['selection'])[sale_order_obj.pretsa_payment_mode]

            #???
            sale_order_schema=prestashop.get('orders',options={'schema':'blank'})
            #blank schema in order
            #update sale_order_schema with following vals presta fields = odoo field using so object
            sale_order_schema['order'].update({
                                               'reference': sale_order_obj.presta_order_ref, 
                                               'module':str(sale_order_obj.pretsa_payment_mode),
                                               'conversion_rate': '1.000000', 
                                               'total_products': str(sale_order_obj.amount_total), 
                                               'total_products_wt': '5.0', 
                                               'id_carrier': sale_order_obj.carrier_prestashop, 
                                               'id_shop_group': '1', 
                                               'id_lang': '1', 
                                               'payment':payment_value,
                                               'current_state': '10', 
#                                               'shipping_number': '', 
                                               'id_shop': '1', 
                                               })

            sale_order_schema['order'].update({'total_paid': str(sale_order_obj.amount_total)})
            if sale_order_obj.invoice_status == 'invoiced':
                
                sale_order_schema['order'].update({'total_paid_tax_incl':str(sale_order_obj.amount_total)})
                sale_order_schema['order'].update({'total_paid_tax_excl':str(sale_order_obj.amount_untaxed)})
                
            
            if sale_order_obj.state=='sale' or sale_order_obj.state=='manual' :
                stock_picking_ids=picking_obj.search([('origin','=',sale_order_obj.name)])
                if stock_picking_ids:
                    stock_obj=picking_obj.browse(stock_picking_ids[0].id)

                    
                    if stock_obj.name:
                        sale_order_schema['order'].update({'delivery_number': stock_obj.name})
                        sale_order_schema['order'].update({'delivery_date': str(stock_obj.min_date)})
                invoice_ids=account_obj.search([('origin','=',sale_order_obj.name)])
                if invoice_ids:
                    inv_state=account_obj.browse(invoice_ids[0].id).state
                    inv_date=account_obj.browse(invoice_ids[0].id).date_invoice
                    if inv_state=='open' or inv_state=='paid':
                        inv_number=account_obj.browse(invoice_ids[0].id).number
                        sale_order_schema['order'].update({'invoice_number': str(inv_number)})
                        sale_order_schema['order'].update({'invoice_date': str(inv_date)})
                        sale_order_schema['order'].update({'total_paid_real':str(sale_order_obj.amount_total)})
                        
    
            if sale_order_obj.partner_id:
                partner_id_list=[sale_order_obj.partner_id.id]
                cust_upld=self.env['prestashop.upload.customer'].create(vals={})
                res=cust_upld.upload_customer(res_ids=partner_id_list,presta_id=presta_inst_id)     
                sale_order_schema['order'].update({'id_customer':res[0][0]})
                sale_order_schema['order'].update({'id_address_delivery':4})
                sale_order_schema['order'].update({'id_address_invoice':res[0][1]})
            
            if sale_order_obj.company_id:
                iso_code=sale_order_obj.company_id.currency_id.name
                currency_ids=prestashop.search('currencies',options={'filter[iso_code]':iso_code})
                sale_order_schema['order'].update({'id_currency':'1'})
                
            sale_line_ids=sale_order_line.search([('order_id','=',rec),('discount','>',0.0)])
            if sale_line_ids:
                for line in sale_line_ids:
                    discount=sale_order_line.browse(line.id).discount
                    sale_order_schema['order'].update({'total_discounts':discount})     
                    sale_order_schema['order'].update({'total_discounts_tax_excl':discount})  
                    
            #instance_obj??
            instance_obj=self.env['prestashop.instance'].browse(1)
            shipping=instance_obj.shipping_product_id 
            if shipping:
                shipping_cost=shipping.list_price
                sale_order_schema['order'].update({'total_shipping':str(shipping_cost)})     
                sale_order_schema['order'].update({'total_shipping_tax_excl':str(shipping_cost)})      
                                                                                    
            order_list=[]
            cart_list=[]
            for order in sale_order_obj.order_line:
                order_line_vals={}
                cart_line_vals={}
                if order.product_id:
                    prod_id=order.product_id.product_tmpl_id
                    product_search_ids=prestashop.search('products',options={'filter[name]':prod_id.name})
                                
                    if not product_search_ids:                                                                           #OR ELSE CREATE IT
                        prd_id_lst=[order.product_id.product_tmpl_id.id]
                        product_upld=self.env['prestashop.upload.products'].create({})
                        product_id=product_upld.upload_products(res_ids=prd_id_lst,presta_id=presta_inst_id)            
                    
#                         product_schema['product'].update({'id':id_product})
                    else:
                        product_id=product_search_ids[0]
#                         product_schema['product'].update({'id':id_product})                    
                    
                    order_line_vals.update({'product_id':product_id})
                    
                    order_line_vals.update({ 
                                         'unit_price_tax_incl': str(order.price_unit), 
                                         'unit_price_tax_excl': str(order.price_unit), 
                                         'product_reference': order.product_id.default_code, 
                                         'product_price': str(order.price_unit), 
                                         'product_quantity': str(int(order.product_uom_qty)), 
                                         #'product_ean13': order.product_id.ean13, 
                                        #'product_attribute_id': '0', 
                                         'product_name': order.product_id.name,     
                                        })
                    
                    order_list.append(order_line_vals)
                    cart_line_vals.update({'id_address_delivery': 4, 
                                           'id_product_attribute': '', 
                                           'id_product': product_id, 
                                           'quantity': str(int(order.product_uom_qty))})
                    cart_list.append(cart_line_vals)
            
            carts_schema=prestashop.get('carts',options={'schema':'blank'})
            carts_schema['cart'].update({
                                         'id_carrier': sale_order_obj.carrier_prestashop, 
                                         'id_shop': '1', 
                                         'id_address_delivery': 4, 
                                         'recyclable': '0', 
                                         'id_customer': res[0][0], 
                                         'id_lang': '1', 
                                         'id_address_invoice': res[0][1], 
                                         'id_shop_group': '1'})

            carts_schema['cart'].update({'id_currency':'1'})
            carts_schema['cart']['associations']['cart_rows'].update({'cart_row':cart_list})   
            sale_order_schema['order']['associations']['order_rows'].update({'order_row':order_list})   
            
            
            sale_gift_ids=sale_order_line.search([('order_id','=',rec),('gift','=',True)])
            if  sale_gift_ids:
                for gift_ids in sale_gift_ids:
                    sale_line_obj=sale_order_line.browse(gift_ids.id)
                    gift_msg=sale_line_obj.gift_message
                    wrapping_cost=sale_line_obj.wrapping_cost
                    carts_schema['cart'].update({'gift':'1','gift_message':gift_msg})
                    sale_order_schema['order'].update({'gift':'1','gift_message':str(gift_msg),'total_wrapping':wrapping_cost,'total_wrapping_tax_excl':wrapping_cost})      
            
            cart_elem=prestashop.add('carts',carts_schema)
            cart_id=cart_elem['prestashop']['cart']['id']            
            if cart_id:
                sale_order_schema['order'].update({'id_cart': cart_id})    
            prestashop.add('orders',sale_order_schema)
    
                