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
from tempfile import TemporaryFile
from odoo import fields,api,models,_
from odoo.exceptions import UserError
import requests
import json
import logging
from datetime import date, datetime, time
logger = logging.getLogger('product')
from odoo.tests import Form
from datetime import date



class GtMagentoStore(models.Model):
    _name= 'gt.magento.store'
    _description = 'Magento Store'
     
     
    name = fields.Char(string='Name',size=64, required=True)
    magento_instance_id = fields.Many2one('gt.magento.instance',string='Instance',readonly=True)
    magento_shop =  fields.Boolean(string='Magento Shop',readonly=True)
    prefix =  fields.Char(string='Prefix', size=64 , default='mag_')
    code =  fields.Char(string='Code', size=64,readonly=True)
    store_id =  fields.Integer(string='Store ID')
    website_id =  fields.Many2one('gt.magento.website',string='Magento Website')
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warhouse')
    discount_product = fields.Many2one('product.product',string='Discount Product')
    shipping_product = fields.Many2one('product.product', string='Shipping Product')
    count_magento_orders = fields.Integer(compute='GetOrdersCount')
    magento_order_date = fields.Date(string="From Date")
    magento_order_date_to = fields.Date(string="To Date")
    source_code = fields.Char(string='Source Code', size=64)
    
    
    def ActionGetOrders(self):
        #print "<================Calling===============>",
        magento_products = self.env['sale.order'].search([('magento_shop_id','=',self.id)])
        #print "<=================Shopify===============>",magento_shop
        action = self.env.ref('globalteckz_magento_2.gt_action_orders_magento')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', magento_products.ids)]
        }

        return result  
    
    def GetOrdersCount(self):
        shop_obj = self.env['sale.order']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_shop_id', '=', shop.id)])
            shop.count_magento_orders = len(multishop_ids.ids)
        return res
    
    
    def GtCreateMagentoOrders(self):

        if not self.shipping_product:
            raise UserError(_('Please, select a shipping product!'))

        partner_id = []
        name = ''
        partner_obj = self.env['res.partner']
        currency_obj=self.env['res.currency']
        payment_obj = self.env['account.payment.term']
        payment_magento_obj = self.env['payment.method.magento']
        delivery_obj = self.env['delivery.carrier']

        if self.magento_instance_id.magento_instance_id_used_token:
            token = self.magento_instance_id.token
        else:
            self.magento_instance_id.generate_token()
            token = self.magento_instance_id.token
            token = token.replace('"'," ")

        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token
            }
        value_date_from = str(self.magento_order_date)
        value_date_to = str(self.magento_order_date_to)
        
        if (value_date_from and value_date_to) == 'False':
            value_date_from = '0000-00-00'
            value_date_to = str(date.today())
        
        if value_date_to and value_date_from:

            if value_date_to >= value_date_from:
                
                url = str(self.magento_instance_id.location) + "/rest/V1/orders? searchCriteria[filterGroups][0][filters][0][field]=created_at& searchCriteria[filterGroups][0][filters][0][value]="+value_date_from+' 00:01:00'+"& searchCriteria[filterGroups][0][filters][0][conditionType]=from& searchCriteria[filterGroups][1][filters][0][field]=created_at& searchCriteria[filterGroups][1][filters][0][value]="+value_date_to+' 23:59:59'+"& searchCriteria[filterGroups][1][filters][0][conditionType]=to& searchCriteria[filterGroups][2][filters][0][field]=store_id& searchCriteria[filterGroups][2][filters][0][value]="+str(self.store_id)+"& searchCriteria[filterGroups][2][filters][0][conditionType]=eq&searchCriteria[page_size]=0"
                response = requests.request("GET",url, headers=headers)
                items=response.json().get("items")
                
                if items:
                    for saleorder_list in items:
                        try:


                            saleordervals = {}
                            payment_term_id = False
                            partner_ship_id = False
                            partner_invoice_id = False

                            saleorder_id = self.env['sale.order'].search([
                                ('mage_order_id', '=', saleorder_list['increment_id']),
                                ('magento_shop_id', '=', self.id)
                            ])

                            if not saleorder_id:

                                payment = payment_obj.search([('name','=','Immediate Payment')])

                                if payment:
                                    payment_term_id = payment.id
                                
                                if saleorder_list['customer_is_guest'] == False:
                                
                                    if 'customer_id' in saleorder_list:
                                        partner_id = partner_obj.search([
                                            ('mag_cust_id','=',saleorder_list['customer_id']),
                                            ('email','=',saleorder_list['customer_email'])
                                            ])
                                        if not partner_id:
                                            url=str(self.magento_instance_id.location)+"/rest/V1/customers/"+str(saleorder_list['customer_id'])
                                            response = requests.request("GET",url, headers=headers)
                                            
                                            if response.status_code == 200:
                                                customer_list = json.loads(response.text)
                                                if customer_list:
                                                    partner_id = self.magento_instance_id.CreateMagentoCustomer(customer_list)
                                                    self._cr.commit()
                                        else:
                                            partner_id = self.GuestCustomer(saleorder_list)
                                    else:
                                        continue

                                    billing_address = saleorder_list['billing_address']
                                    if billing_address.get('customer_address_id'):
                                        if 'customer_id' in saleorder_list:
                                            street,street1='',''
                                            partner_invoice_id = partner_obj.search([
                                                ('mag_cust_id','=',saleorder_list['customer_id']),
                                                ('mag_address_id','=',billing_address.get('customer_address_id'))
                                                ])
                    
                                            if not partner_invoice_id:

                                                if 'customer_address_id' in billing_address:
                                                    id = billing_address.get('customer_address_id')
                                                    url=str(self.magento_instance_id.location)+"/rest/V1/customers/addresses/"+str(id)
                                                    response = requests.request("GET",url, headers=headers)
                                                    
                                                    if response.status_code == 200:
                                                        cust_address = json.loads(response.text)
                                                        if cust_address:
                                                            partner_invoice_id = self.create_customer_address(cust_address,partner_id)
                                                            self._cr.commit()
                                                else:

                                                    if billing_address.get('street',False):
                                                        street=billing_address.get('street',False)[0]
                                                        if len(billing_address.get('street',False))==2:
                                                            street1= billing_address.get('street',False)[1]
                                                            street1= cust_address.get('street',False)[1]
                                        
                                                    partner_invoice_id = partner_obj.search([
                                                        ('mag_cust_id','=',saleorder_list['customer_id']),
                                                        ('name','=',billing_address.get("firstname",False) + ' ' + billing_address.get("lastname",False)),
                                                        ('street','=',street),
                                                        ('street2','=',street1)
                                                        ])
                                                    
                                                    if not partner_invoice_id:
                                                        partner_invoice_id = self.temporary_address(billing_address,partner_id)
                                        else:
                                            partner_invoice_id = self.GuestCustomerInvoice(saleorder_list['billing_address'],partner_id)

                                    shipping_address = saleorder_list['extension_attributes']['shipping_assignments'][0]

                                    odoo_partner_addresses = partner_id.child_ids
                                    magento_partner_address = shipping_address['shipping']
                                    addresses_zip = []
                                    addresses_street = []


                                    for address in odoo_partner_addresses:
                                        addresses_zip.append(address.zip)
                                        addresses_street.append(address.street)

                                    if magento_partner_address['address']['postcode'] not in addresses_zip:
                                        exist_zip = True
                                    else:
                                        exist_zip = False

                                    if magento_partner_address['address']['street'][0] not in addresses_street:
                                        exist_street = True
                                    else:
                                        exist_street = False

                                    if exist_zip and exist_street:
                                        mag_address = magento_partner_address['address']
                                        shipping_id = self.temporary_address(mag_address,partner_id)
                                    
                                    else: 
                                        for ship in odoo_partner_addresses:
                                            if magento_partner_address['address']['postcode'] == ship.zip:
                                                shipping_id = ship

                                    if 'shipping' in shipping_address:
                                        
                                        shipp_addre = shipping_address['shipping']

                                        if 'address' in shipp_addre:
                                            shipp_address = shipp_addre['address']
                                            
                                            if 'customer_id' in saleorder_list:
                                                
                                                if shipp_address:

                                                    street,street1='',''
                                                    partner_ship_id = partner_obj.search([
                                                        ('mag_cust_id','=',saleorder_list['customer_id']),
                                                        ('mag_address_id','=',shipp_address.get('customer_address_id'))
                                                        ])
                                                    
                                                    if not partner_ship_id:
                                                        if shipp_address.get('customer_address_id') != 0 :
                                                            id = shipp_address.get('customer_address_id')
                                                            url=str(self.magento_instance_id.location)+"/rest/V1/customers/addresses/"+str(id)        
                                                            response = requests.request("GET",url, headers=headers)
                                                            if response.status_code == 200:
                                                                cust_address = json.loads(response.text)
                                                                if cust_address:
                                                                    partner_ship_id = self.create_customer_address(cust_address,partner_id)
                                                        else:
                                                            if len(shipp_address.get('street',False)):
                                                                street,street1=False,False
                                                                street=shipp_address.get('street',False)[0]
                                                                if len(shipp_address.get('street',False))==2:
                                                                    street1=shipp_address.get('street',False)[1]
                                                                name = shipp_address.get("firstname",False) + ' ' + shipp_address.get("lastname",False)
                                                            partner_ship_id = partner_obj.search([
                                                                ('mag_cust_id','=',saleorder_list['customer_id']),
                                                                ('name','=',name),('street','=',street),
                                                                ('street2','=',street1)
                                                                ])
                                                            if not partner_ship_id:
                                                                if shipp_address and partner_id:
                                                                    partner_ship_id = self.temporary_address(shipp_address,partner_id)
                                        else:
                                            partner_ship_id = self.GuestCustomerDelivery(shipp_address,partner_id)
                                else:
                                    partner_id = self.GuestCustomer(saleorder_list)
                                    if 'billing_address' in saleorder_list:
                                        partner_invoice_id = self.GuestCustomerInvoice(saleorder_list['billing_address'],partner_id)
                                    shipping_address = saleorder_list['extension_attributes']['shipping_assignments'][0]
                                    if 'shipping' in shipping_address:
                                        shipp = shipping_address['shipping']
                                        if 'address' in shipp:
                                            shipp_address = shipp['address']
                                            partner_ship_id = self.GuestCustomerDelivery(shipp_address,partner_id)
                                payment_method=saleorder_list['payment']['method']
                                
                                if payment_method:
                                    
                                    payment_magento_obj.create_payment_method(self,headers,saleorder_list['payment']['entity_id'])
                                    payment_id=payment_magento_obj.search([('code','=',payment_method)])
                                
                                delivery_id = []
                                
                                if 'shipping_description' in saleorder_list:
                                    delivery_id = delivery_obj.search([('name','=',str(saleorder_list['shipping_description']))])
                                    if not delivery_id:
                                        value_delivery = {
                                            'delivery_type': 'fixed',
                                            'invoice_policy': 'real', 
                                            'name': str(saleorder_list['shipping_description']),
                                            'product_id': self.shipping_product.id,
                                            'mage_delivery':True,
                                            'fixed_price':float(saleorder_list['base_shipping_amount'])
                                            } 
                                        delivery_id = delivery_obj.create(value_delivery).id
                                        self.env.cr.commit()

                                if partner_id:
                                    
                                    if shipping_id: 
                                        id_ship = shipping_id.id
                                    else:
                                        id_ship = partner_ship_id.id if partner_ship_id else partner_id[0].id


                                    value_saleordervals = {
                                        'partner_id': partner_id[0].id,
                                        'partner_invoice_id': partner_invoice_id.id if partner_invoice_id else partner_id[0].id, 
                                        'partner_shipping_id': id_ship,
                                        'name': str(saleorder_list['increment_id']),
                                        'mage_order_id': str(saleorder_list['increment_id']),
                                        'magento_shop_id': self.id,
                                        'order_status': str(saleorder_list['status']),
                                        'date_order': saleorder_list['created_at'],
                                        'order_date': saleorder_list['created_at'],
                                        'entity_id':  saleorder_list.get('entity_id') or False,
                                        'ma_order_id': saleorder_list['items'][0]['order_id'],
                                        'magento_order':  True,
                                        'payment_term_id': payment_term_id or False,
                                        'payment_method': payment_id.id or False, 
                                        'carrier_id': delivery_id.id or False, 
                                        'company_id': self.env.company.id,
                                        'currency_id': self.env.company.currency_id.id,
                                    }

                                    saleordervals = value_saleordervals

                                    if self.warehouse_id:
                                        saleordervals['warehouse_id'] = self.warehouse_id.id

                                    if self.pricelist_id:
                                        saleordervals['pricelist_id'] = self.pricelist_id.id

                                    saleorder_id = self.env['sale.order'].create(saleordervals)
                                    self.env.cr.commit()
                                    
                                    disc_tax_id = []
                                    
                                    for each_result in saleorder_list['items']:
                                        if each_result.get('product_type')=='configurable':
                                            continue
                                        else :
                                            product_id = []
                                            orderlinevals = {}

                                            product_ids = self.env['product.product'].search([('default_code','=',str(each_result['sku']))], limit=1)
                                            
                                            if not product_ids:

                                                sku = each_result['sku']
                                                instance = self.magento_instance_id
                                                store = self
                                                website = self.website_id
                                                magento_product_id = each_result['product_id']
                                                if sku and instance and store and website and magento_product_id:
                                                    product_id = self.env['product.product'].create_simple_products_orders(instance,headers,sku,store,website,magento_product_id)
                                                    self.env.cr.commit()
                                            
                                                    if not product_id:
                                                        
                                                        product_ids = self.env['product.product'].search([('default_code','=','deleted_product')])
                                                        if not product_ids:
                                                            vals = {
                                                                'name':'Product Removed or Deleted',
                                                                'default_code':'deleted_product'
                                                                }
                                                            product_id = self.env['product.product'].create(vals)
                                                            self.env.cr.commit()
                                            else:
                                                product_id = product_ids

                                        if 'parent_item'in each_result:
                                            parent_item = each_result['parent_item']
                                            if 'base_price' in parent_item and  parent_item['base_price'] > 0:
                                                unit_price = parent_item['base_price']
                                        else:
                                            unit_price = each_result['base_price']

                                        orderlinevals = {
                                            'name': name or product_id.name,
                                            'order_id': saleorder_id.id,
                                            'price_unit': float(unit_price) ,
                                            'product_uom_qty': float(each_result['qty_ordered']),
                                            'product_uom': product_id[0].product_tmpl_id.uom_id.id,
                                            'product_id': product_id[0].id,
                                            'order_item_id':str(each_result['item_id']),
                                            }
                                        tax_id = []
                                        if each_result.get('tax_percent') != None:
                                            tax_id = self.getTaxesAccountID(each_result)
                                            if tax_id:
                                                orderlinevals['tax_id'] = [(6, 0, tax_id)]
                                            else:
                                                orderlinevals['tax_id'] =[(6, 0, [])]
                                        else:
                                            orderlinevals['tax_id'] =[(6, 0, [])]
                                        
                                        self.env['sale.order.line'].create(orderlinevals)
                                        self.env.cr.commit()
                                        
                                        disc_tax_id = tax_id
                                    
                                    if float(saleorder_list['discount_amount']) != 0.00 :
                                        
                                        discount = 0
                                        
                                        if not self.discount_product:
                                            raise UserError(_('Please Configure Discount Product!'))
                                        
                                        if float(saleorder_list['discount_amount']) > 0:
                                            discount = float(saleorder_list['discount_amount'])
                                        else:
                                            if 'discount_invoiced' in saleorder_list and float(saleorder_list['discount_invoiced']) != 0.00:
                                                discount = float(saleorder_list['discount_invoiced'])
                                        
                                        prod_discount_product = self.discount_product
                                        discountorderlinevals = {
                                            'order_id' : saleorder_id.id,
                                            'product_uom_qty' : 1,
                                            'product_uom' : prod_discount_product.product_tmpl_id.uom_id.id,
                                            'name' : prod_discount_product.name,
                                            'price_unit' : discount,
                                            'product_id' : prod_discount_product.id,
                                            'tax_id': [(6, 0, disc_tax_id)],
                                        }
                                        self.env['sale.order.line'].create(discountorderlinevals)
                                        self.env.cr.commit()

                                    if 'shipping_amount' in saleorder_list:

                                        prod_shipping_product = self.shipping_product
                                        shipping_line_vals = {
                                            'order_id' : saleorder_id.id,
                                            'product_uom_qty' : 1,
                                            'product_uom' : prod_shipping_product.product_tmpl_id.uom_id.id,
                                            'name' : delivery_id.name if delivery_id else prod_shipping_product.name,
                                            'price_unit' : saleorder_list['shipping_amount'],
                                            'product_id' : prod_shipping_product.id,
                                            'tax_id': [(6, 0, disc_tax_id)],
                                        }
                                        self.env['sale.order.line'].create(shipping_line_vals)
                                        self.env.cr.commit()

                        except Exception as exc:
                            logger.error("======== Error : %s" % exc)
                            
                    vals_d = {
                        'magento_order_date':date.today(),
                        'magento_order_date_to':date.today()
                        }
                    self.write(vals_d)

        return True




    def GuestCustomer(self, saleorder_list):
        PartnerObj = self.env['res.partner']
        partner_id = PartnerObj.search([('email', '=', saleorder_list['customer_email'])])
        if not partner_id:
            vals = {'name': saleorder_list['customer_firstname'] + ' ' + saleorder_list['customer_lastname'],
                    'email': saleorder_list['customer_email'],
                    }
            partner_id = PartnerObj.create(vals)
            self._cr.commit()
        return partner_id

    def GuestCustomerInvoice(self, cust_address, partner_id):
        partner_vals = {}
        PartnerObj = self.env['res.partner']
        partner_invoice_id = PartnerObj.search(
            [('parent_id', '=', partner_id.id), ('mag_address_id', '=', cust_address['entity_id'])])
        if not partner_invoice_id:
            country_id = self.env['res.country'].search([('code', '=', cust_address.get("country_id", False))])
            if country_id:
                partner_vals.update({'country_id': country_id.id})
                if 'region_code' in cust_address:
                    state_code = cust_address["region"] if 'region' in cust_address else ''
                    if state_code:
                        state_ids = self.env['res.country.state'].search(
                            [('code', '=', state_code), ('country_id', '=', country_id.id)])
                        state_id = []
                        if not state_ids:
                            state_id = self.env['res.country.state'].create({
                                'code': state_code,
                                'name': cust_address["region"]["region"],
                                'country_id': country_id.id
                            })
                        else:
                            state_id = state_ids[0].id
                        partner_vals.update({'state_id': state_id.id})
            if len(cust_address.get('street', False)):
                street, street1 = False, False
                street = cust_address.get('street', False)[0]
            if len(cust_address.get('street', False)) == 2:
                street1 = cust_address.get('street', False)[1]
                partner_vals.update({'street': street, 'street2': street1})
            if cust_address.get('defaultShipping', False):
                partner_vals.update({'type': 'delivery'})
            elif cust_address.get('defaultBilling', False):
                partner_vals.update({'type': 'invoice'})
            else:
                partner_vals.update({'type': 'other'})
            partner_vals.update({
                'mag_address_id': cust_address.get(str('id')),
                'name': cust_address.get("firstname", False) + ' ' + cust_address.get("lastname", False),
                'phone': cust_address.get('telephone', False),
                'zip': cust_address.get('postcode', False),
                'city': cust_address.get('city', False),
                'magento_customer': True,
                'mag_cust_id': cust_address.get(str('customer_id')),
                'parent_id': partner_id.id})
            partner_invoice_id = self.env['res.partner'].create(partner_vals)

        return partner_invoice_id

    def GuestCustomerDelivery(self, cust_address, partner_id):
        partner_vals = {}
        PartnerObj = self.env['res.partner']
        partner_delivery_id = PartnerObj.search(
            [('parent_id', '=', partner_id.id), ('mag_address_id', '=', cust_address['entity_id'])])
        print("partner_invoice_id+__+_+_+_+_+_+_guest customer", partner_delivery_id)
        if not partner_delivery_id:
            country_id = self.env['res.country'].search([('code', '=', cust_address.get("country_id", False))])
            if country_id:
                partner_vals.update({'country_id': country_id.id})
                if 'region_code' in cust_address:
                    state_code = cust_address["region"] if 'region' in cust_address else ''
                    if state_code:
                        state_ids = self.env['res.country.state'].search(
                            [('code', '=', state_code), ('country_id', '=', country_id.id)])
                        state_id = []
                        if not state_ids:
                            state_id = self.env['res.country.state'].create({
                                'code': state_code,
                                'name': cust_address["region"]["region"],
                                'country_id': country_id.id
                            })
                        else:
                            state_id = state_ids[0].id
                        partner_vals.update({'state_id': state_id.id})
            if len(cust_address.get('street', False)):
                street, street1 = False, False
                street = cust_address.get('street', False)[0]
            if len(cust_address.get('street', False)) == 2:
                street1 = cust_address.get('street', False)[1]
                partner_vals.update({'street': street,
                                     'street2': street1})
            if cust_address.get('address_type', False) == 'shipping':
                partner_vals.update({'type': 'delivery'})
            elif cust_address.get('defaultBilling', False) == 'billing':
                partner_vals.update({'type': 'invoice'})
            else:
                partner_vals.update({'type': 'other'})

            partner_vals.update({
                'mag_address_id': cust_address.get(str('id')),
                'name': cust_address.get("firstname", False) + ' ' + cust_address.get("lastname", False),
                'phone': cust_address.get('telephone', False),
                'zip': cust_address.get('postcode', False),
                'city': cust_address.get('city', False),
                'magento_customer': True,
                'mag_cust_id': cust_address.get(str('customer_id')),
                'parent_id': partner_id.id})
            partner_delivery_id = self.env['res.partner'].create(partner_vals)
            # print("partner_invoice_id+__+_+_+_+_+_+_guest customer",partner_delivery_id)
            return partner_delivery_id

    def getTaxesAccountID(self,each_result):
        accounttax_obj = self.env['account.tax']
        accounttax_id = []
        shop_data = self.browse(self._ids)
        amount = float(each_result['tax_percent'])
        acctax_ids = accounttax_obj.search([('type_tax_use', '=', 'sale'),('amount', '=', amount)])

        if not len(acctax_ids):
            accounttax_id = accounttax_obj.create({'name':'Sales Tax(' + str(each_result['tax_percent']) + '%) ','amount':amount,'type_tax_use':'sale'})
            accounttax_id = accounttax_id.id
        else:
            accounttax_id = acctax_ids[0].id

        return [accounttax_id]
    
    
    
    def temporary_address(self,cust_address,partner_id):
        partner_vals={}
        print ("cust_address++++++++++",cust_address)
        country_id=self.env['res.country'].search([('code','=',cust_address.get("country_id",False))])
        if country_id:
            partner_vals.update({'country_id':country_id.id})
            if cust_address.get('region_code'):
                state_code = cust_address.get('region_code')
                state_ids=self.env['res.country.state'].search([('code','=',state_code),('country_id','=',country_id.id)])
                if not state_ids:
                    state_id=self.env['res.country.state'].create({
                        'code':state_code,
                        'name':cust_address.get("region"),
                        'country_id':country_id.id
                        })
                    partner_vals.update({ 'state_id':state_id.id})
                else:
                    state_id = state_ids[0].id
        if len(cust_address.get('street',False)):
            street,street1=False,False
            street=cust_address.get('street',False)[0]
            if len(cust_address.get('street',False))==2:
                street1=cust_address.get('street',False)[1]
            partner_vals.update({'street':street,
                                'street2':street1})
        if cust_address.get('address_type',False) == 'shipping': 
            partner_vals.update({'type': 'delivery'})
        elif cust_address.get('defaultBilling',False) == 'billing':
            partner_vals.update({'type': 'invoice'})
        else:
            partner_vals.update({'type': 'other'})

        partner_vals.update({
            'mag_address_id':cust_address.get(str('id')),
            'name':cust_address.get("firstname",False) + ' ' + cust_address.get("lastname",False),
            'phone':cust_address.get('telephone',False),
            'zip':cust_address.get('postcode',False),
            'city':cust_address.get('city',False),
            'magento_customer': True,
            'mag_cust_id':cust_address.get(str('customer_id')),
            'parent_id':partner_id.id})
        partnerss_id = self.env['res.partner'].create(partner_vals)
        
        print ("partnerss_id+++++++++++",partnerss_id)
        
        self._cr.commit()
        
        return partnerss_id
    
    
    def create_customer_address(self,cust_address,partner_id):
        
        print ("partner_id++++++++creatingin address",partner_id)
        partner_vals={}
        company = []
        print ("cust_address+++++++++++",cust_address)
        country_id=self.env['res.country'].search([('code','=',cust_address.get("country_id",False))])
        if country_id:
            partner_vals.update({'country_id':country_id.id})
            if cust_address.get("region",False)['region_code']:
                state_code = cust_address["region"]["region_code"]
                state_ids=self.env['res.country.state'].search([('code','=',state_code),('country_id','=',country_id.id)])
                if not state_ids:
                    state_id=self.env['res.country.state'].create({
                        'code':state_code,
                        'name':cust_address["region"]["region"],
                        'country_id':country_id.id
                        })
                    partner_vals.update({ 'state_id':state_id.id})
                else:
                    state_id = state_ids[0].id
        if cust_address.get('street',False):
            street,street1=False,False
            street=cust_address.get('street',False)[0]
            if len(cust_address.get('street',False))==2:
                street1=cust_address.get('street',False)[1]
            partner_vals.update({'street':street,
                                'street2':street1})
        if cust_address.get('defaultShipping',False):
            partner_vals.update({'type': 'delivery'})
        elif cust_address.get('defaultBilling',False):
            partner_vals.update({'type': 'invoice'})
        else:
            partner_vals.update({'type': 'other'})

        partner_vals.update({
            'mag_address_id':cust_address.get(str('id')),
            'name':cust_address.get("firstname",'') + cust_address.get("lastname",''),
            'phone':cust_address.get('telephone',False),
            'zip':cust_address.get('postcode',False),
            'city':cust_address.get('city',False),
            'magento_customer': True,
            'mag_cust_id':cust_address.get(str('customer_id')),
            'parent_id':partner_id.id})
        partner_invoice_id = self.env['res.partner'].create(partner_vals)
        print ("partner_invoice_id+++++++++",partner_invoice_id)
       
        self._cr.commit()
       
        return partner_invoice_id


    
    def GtCreateMagentoInvoice(self):

        account_invoice_obj = self.env['account.move']
        
        self.magento_instance_id.generate_token()
        token=self.magento_instance_id.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token
            }
        url=str(self.magento_instance_id.location)+"/rest/V1/invoices?searchCriteria[filterGroups][0][filters][0][field]=store_id& searchCriteria[filterGroups][0][filters][0][value]=%s& searchCriteria[filterGroups][0][filters][0][conditionType]=eq&searchCriteria[page_size]=0"%(self.store_id,)
        response = requests.request("GET",url, headers=headers)
        items=response.json().get("items")
        for invoice_list in items:
            try:
                invoice_ids = account_invoice_obj.search([('mage_invoice_id','=',invoice_list['increment_id'])])
                # import wdb
                # wdb.set_trace()
                if not invoice_ids: 
                    sale_id=self.env['sale.order'].search([('ma_order_id','=',invoice_list['order_id'])])
                    if sale_id:
                        if not sale_id.invoice_ids:
                            sale_id.action_confirm()
                            self._cr.commit()
                            sale_id._create_invoices()
                            self._cr.commit()
                            for invoice_id in sale_id.invoice_ids:
                                # invoice_id.action_invoice_open()
                                if sale_id.payment_method:
                                    journal_id = self.env['account.journal'].search([('name','=',sale_id.payment_method.name.lower()),('code','=',sale_id.payment_method.name[:4].lower())], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':sale_id.payment_method.name.lower(),'type':'bank','code':sale_id.payment_method.name[:4].lower()})
                                else:
                                    journal_id = self.env['account.journal'].search([('name','=','Magento Payment'),('code','=','MAGENTO')], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':'Magento Payment','type':'bank','code': 'MAGENTO'})
                                # invoice_id.pay_and_reconcile(journal_id,invoice_id.amount_total)                                  
                                invoice_id.write({
                                    'mage_invoice_id': invoice_list['increment_id'],
                                    })
                            sale_id.write({'invoiced': True,})
                            self._cr.commit()

                    if sale_id.picking_ids:
                        if sale_id.invoice_ids.state=='paid' and sale_id.picking_ids[0].state=='done' and sale_id.order_status=='complete':
                            sale_id.action_done()
                    self._cr.commit()

            except Exception as exc:
                logger.error('Exception ===================:  %s', exc)
                
        return True
    
    
    
    def GtCreateMagentoShipment(self):
       # try:
        self.magento_instance_id.generate_token()
        token=self.magento_instance_id.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token
            }
        url=str(self.magento_instance_id.location)+"/rest/V1/shipments?searchCriteria[filterGroups][0][filters][0][field]=store_id& searchCriteria[filterGroups][0][filters][0][value]=%s& searchCriteria[filterGroups][0][filters][0][conditionType]=eq&searchCriteria[page_size]=0"%(self.store_id,)
        response = requests.request("GET",url, headers=headers)
        items=response.json().get("items")
        print ("items+++++++++++++++",items)
        print ("no of pick",len(items))
        if items:
            for shipment_list in items:
                try:
                    ship_id =self.env['stock.picking'].search([('mage_stock_id','=',shipment_list['increment_id'])])
                    if not ship_id:
                        sale_id=self.env['sale.order'].search([('ma_order_id','=',shipment_list['order_id'])])
                        if sale_id:
                            if not sale_id.picking_ids:
                                sale_id.action_confirm()
                                for picking_id in sale_id.picking_ids:
                                    picking_id.action_confirm()
                                    picking_id.action_assign()
                                    # picking_id.force_assign()
                                    # picking_id.do_transfer()
                                    picking_id.write({'mage_stock_id':shipment_list['increment_id']})
                                sale_id.write({'shipped': True})
                                if sale_id.invoice_ids.state=='paid' and picking_id.state=='done' and sale_id.order_status=='complete':
                                    sale_id.action_done()
                            else:
                                for picking_id in sale_id.picking_ids:
                                    picking_id.action_confirm()
                                    picking_id.action_assign()
                                    # picking_id.force_assign()
                                    # picking_id.do_transfer()
                                    picking_id.write({'mage_stock_id':shipment_list['increment_id']})
                                sale_id.write({'shipped': True})
                                if sale_id.invoice_ids.state=='paid' and picking_id.state=='done' and sale_id.order_status=='complete':
                                    sale_id.action_done()
                except Exception as exc:
                    logger.error('========  Error :  %s', exc)
                        
        return True
    

    def GtExportMagentoInvoice(self):
        
        token = False
       
        if self.magento_instance_id.magento_instance_id_used_token:
            token = self.magento_instance_id.token
        else:
            self.magento_instance_id.generate_token()
            token = self.magento_instance_id.token
            token = token.replace('"'," ")

        account_invoice_obj = self.env['account.move']
        
        sale_obj = self.env['sale.order']
        headers = {
            'authorization':"Bearer "+token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }
        
        sale_ids = sale_obj.search([('magento_shop_id','=',self.id),('state','!=', 'sent'),'|',('order_status','=','pending'),('order_status','=','processing'),('invoiced','=',False)])
            
        for sale_id in sale_ids:
          
            invoice_id = account_invoice_obj.search([('invoice_origin','=',sale_id.name)])
            
            self.export_magento_invoice_order(headers, invoice_id, sale_id)
    
    def GtExportMagentoShipment(self):
        
        token = False
       
        if self.magento_instance_id.magento_instance_id_used_token:
            token = self.magento_instance_id.token
        else:
            self.magento_instance_id.generate_token()
            token = self.magento_instance_id.token
            token = token.replace('"'," ")
        
        sale_obj = self.env['sale.order']
        stock_obj = self.env['stock.picking']

        headers = {
            'authorization':"Bearer " + token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }

        sale_ids = sale_obj.search([('magento_shop_id','=',self.id),'|',('order_status','=','pending'),('order_status','=','processing'),('shipped','=',False)])

        for sale_id in sale_ids:
        
            stock_id = stock_obj.search([('origin','=',sale_id.name)])
            self.export_magento_shipment_order(headers, stock_id, sale_id)


    def export_magento_shipment_order(self, headers, stock_id, sale_id):

        shop_data = self
        try:

            if stock_id:
                
                item = []
                
                for line in sale_id.order_line:
                    if line.product_id != self.shipping_product:
                        if line.product_id.type != 'service':
                            item.append({
                                "order_item_id":line.order_item_id,
                                "qty":line.product_uom_qty,
                                "extension_attributes": {},
                            })

                vals = {
                    "entity": {
                        "order_id": sale_id.entity_id,
                        "items": item,
                    }
                }

                if stock_id[0].carrier_tracking_ref:
                    if stock_id[0].carrier_id.magento_code:
                        vals.update({"tracks": [
                                {
                                "extension_attributes": {},
                                "track_number":stock_id[0].carrier_tracking_ref or False,
                                "title":stock_id[0].carrier_id.name or False,
                                "carrier_code":stock_id[0].carrier_id.magento_code or False,
                                }
                            ],})

                payload = str(vals) 
                payload=payload.replace("'",'"')     
                payload=str(payload).replace('u"','"')
                
                url = shop_data.magento_instance_id.location+"/rest/"+ str(sale_id.magento_shop_id.code) +"/V1/order/" + sale_id.entity_id +"/ship" 
                
                response = requests.request("POST",url, data=payload, headers=headers)
                
                if str(response.status_code)=="200":
                    each_response=json.loads(response.text)
                    if sale_id.invoiced == True:
                        sale_id.write({'shipped': True,'order_status': 'complete'})
                    else:
                        sale_id.write({'shipped': True,'order_status': 'processing'})

                    return 'sucess'

        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            pass   

    def export_magento_invoice_order(self, headers, invoice_id, sale_id):
        
        shop_data = self   
        try:
            
            
            for invoice in invoice_id:
                if invoice.state=='cancel':
                    continue
                item = []

                for invoice_line in  invoice.invoice_line_ids:
                    if invoice_line.product_id.type == 'product':

                        item.append({
                            "order_item_id": invoice_line.sale_line_ids[0].order_item_id,
                            "qty": invoice_line.quantity,
                            "extension_attributes": {}
                        })
                    
                vals = {
                    "entity": {
                        "order_id": sale_id.entity_id,
                        "items": item,
                    }
                }
                    
                payload = str(vals) 
                payload=payload.replace("'",'"')  
                payload=str(payload).replace('u"','"')
                url=shop_data.magento_instance_id.location+"/rest/"+ str(sale_id.magento_shop_id.code) +"/V1/order/" + sale_id.entity_id +"/invoice"

                response = requests.request("POST",url, data=payload, headers=headers)

                if str(response.status_code)=="200":
                    each_response = json.loads(response.text)
                    if sale_id.shipped == True:
                        sale_id.write({'invoiced': True,'order_status': 'complete'})
                    else:
                        sale_id.write({'invoiced': True,'order_status': 'processing'})

                    return 'sucess'
        
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            pass   