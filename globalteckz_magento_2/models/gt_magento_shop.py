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
from odoo import fields,api,models,_
from odoo.exceptions import UserError
import requests
import json
import logging
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
        partner_obj = self.env['res.partner']
        currency_obj=self.env['res.currency']
        payment_obj = self.env['account.payment.term']
        payment_magento_obj = self.env['payment.method.magento']
        delivery_obj = self.env['delivery.carrier']
        self.magento_instance_id.generate_token()
        token=self.magento_instance_id.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token
            }
        value_date_from = str(self.magento_order_date)
        value_date_to = str(self.magento_order_date_to)
        if value_date_to and value_date_from:
            if value_date_to >= value_date_from:
                url=str(self.magento_instance_id.location)+"/rest/V1/orders? searchCriteria[filterGroups][0][filters][0][field]=created_at& searchCriteria[filterGroups][0][filters][0][value]="+value_date_from+' 00:01:00'+"& searchCriteria[filterGroups][0][filters][0][conditionType]=from& searchCriteria[filterGroups][1][filters][0][field]=created_at& searchCriteria[filterGroups][1][filters][0][value]="+value_date_to+' 23:59:59'+"& searchCriteria[filterGroups][1][filters][0][conditionType]=to& searchCriteria[filterGroups][2][filters][0][field]=store_id& searchCriteria[filterGroups][2][filters][0][value]="+str(self.store_id)+"& searchCriteria[filterGroups][2][filters][0][conditionType]=eq"
                print ("url_)_)_)_)_)_)_",url)
                response = requests.request("GET",url, headers=headers)
                items=response.json().get("items")
                print ("response+_+_+_+_+_+_+_+_items",len(items))
                for saleorder_list in items:
                    print ("saleorder_list+_+_+_+_+_+_+_",saleorder_list)
                    saleordervals = {}
                    payment_term_id = []
                    partner_ship_id = []
                    partner_invoice_id = []
                    saleorder_id=self.env['sale.order'].search([('mage_order_id','=',saleorder_list['increment_id']),('magento_shop_id','=',self.id)])
                    if not saleorder_id:
                        payment = payment_obj.search([('name','=','Immediate Payment')])
                        if payment:
                            payment_term_id = payment.id
                        if saleorder_list['customer_is_guest'] == False:
                            if 'customer_id' in saleorder_list:
                                partner_id = partner_obj.search([('mag_cust_id','=',saleorder_list['customer_id']),('email','=',saleorder_list['customer_email'])])
                                #print ("partner_id+++++++++++0",partner_id)
                                if not partner_id:
                                    url=str(self.magento_instance_id.location)+"rest/V1/customers/"+str(saleorder_list['customer_id'])
                                    #print ("url+++++++++++++++++++++++c ustom",url)
                                    response = requests.request("GET",url, headers=headers) 
                                    #print ("response++++++++++++",response)
                                    customer_list=json.loads(response.text)
                                    #print ("customer_list++++++++++++++++",customer_list)
                                    partner_id = self.magento_instance_id.CreateMagentoCustomer(customer_list)
                                    #print ('partner_id++++++++++order',partner_id[0])
                                    self._cr.commit()
                                else:
                                    partner_id = self.GuestCustomer(saleorder_list)
                            billing_address = saleorder_list['billing_address']
                            if billing_address.get('customer_address_id'):
                                if 'customer_id' in saleorder_list:
                                    street,street1='',''
                                    partner_invoice_id = partner_obj.search([('mag_cust_id','=',saleorder_list['customer_id']),('mag_address_id','=',billing_address.get('customer_address_id'))])
                                    #print ("partner_invoice_id6++++++",partner_invoice_id)
                                    if not partner_invoice_id:
                                        #print ("billing_address++++++++++++++",billing_address)
                                        if 'customer_address_id' in billing_address:
                                            url=str(self.magento_instance_id.location)+"rest/V1/customers/addresses/"+str(billing_address.get('customer_address_id'))
                                            #print ("url+++++++++++++++++++++++",url)
                                            response = requests.request("GET",url, headers=headers) 
            #                                print ("response++++++++",response)
            #                                print ("response++++++++++++",json.loads(response.text))
                                            partner_invoice_id = self.create_customer_address(json.loads(response.text),partner_id)
                                        else:
                                            #print ("billing_address++_+_+_+_+_+",billing_address)
                                            if billing_address.get('street',False):
                                                street=billing_address.get('street',False)[0]
                                                if len(billing_address.get('street',False))==2:
                                                    street1=cust_address.get('street',False)[1]
                                                #print ("street+++++++++++",street,street1)
                                        partner_invoice_id = partner_obj.search([('mag_cust_id','=',saleorder_list['customer_id']),('name','=',billing_address.get("firstname",False) + ' ' + billing_address.get("lastname",False)),('street','=',street),('street2','=',street1)])
                                        #print ("partner_invoice_id|||||||",partner_invoice_id)
                                        if not partner_invoice_id:
                                            partner_invoice_id = self.temporary_address(billing_address,partner_id)
                                else:
                                    partner_invoice_id = self.GuestCustomerInvoice(saleorder_list['billing_address'],partner_id)
                            shipping_address = saleorder_list['extension_attributes']['shipping_assignments'][0]
                            #print ("shipping_address++++++++++",shipping_address)
                            if 'shipping' in shipping_address:
                                shipp_addre = shipping_address['shipping']
                                if 'address' in shipp_addre:
                                    shipp_address = shipp_addre['address']
                                #print ("shipp_address++++++++++++",shipp_address)
                                    if 'customer_id' in saleorder_list:
                                        if shipp_address:
                                            street,street1='',''
                                            partner_ship_id = partner_obj.search([('mag_cust_id','=',saleorder_list['customer_id']),('mag_address_id','=',shipp_address.get('customer_address_id'))])
                                            #print ("partner_invoice_id6++++++",partner_invoice_id)
                                            if not partner_ship_id:
                                                if shipp_address.get('customer_address_id') != 0 :
                                                    url=str(self.magento_instance_id.location)+"/rest/V1/customers/addresses/"+str(shipp_address.get('customer_address_id'))
                                                    #print ("url+++++++++++++++++",url)
                                                    response = requests.request("GET",url, headers=headers) 
                                                    #print ("response++++++++++++",json.loads(response.text))
                                                    partner_ship_id = self.create_customer_address(json.loads(response.text),partner_id)
                                                else:
                                                    if len(shipp_address.get('street',False)):
                                                        street,street1=False,False
                                                        street=shipp_address.get('street',False)[0]
                                                        if len(shipp_address.get('street',False))==2:
                                                            street1=shipp_address.get('street',False)[1]
                                                        #print ("street+++++++++++",street,street1)
                                                        name = shipp_address.get("firstname",False) + ' ' + shipp_address.get("lastname",False)
                                                    partner_ship_id = partner_obj.search([('mag_cust_id','=',saleorder_list['customer_id']),('name','=',name),('street','=',street),('street2','=',street1)])
                                                    if not partner_ship_id:
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
                        logger.error('partner_id---------------  %s', partner_id)
                        logger.error('partner_invoice_id---------------  %s', partner_invoice_id)
                        logger.error('partner_ship_id---------------  %s', partner_ship_id)
                        payment_method=saleorder_list['payment']['method']
                        if payment_method:
                            payment_magento_obj.create_payment_method(self,headers,saleorder_list['payment']['entity_id'])
                            payment_id=payment_magento_obj.search([('code','=',payment_method)])
                        delivery_id = []
                        if 'shipping_description' in saleorder_list:
                            delivery_id = delivery_obj.search([('name','=',str(saleorder_list['shipping_description']))])
                            #print ("delivery_id+++++++++++",delivery_id)
                            if not delivery_id:
                                delivery_id = delivery_obj.create({'name': str(saleorder_list['shipping_description']), 'mage_delivery':True,'fixed_price':float(saleorder_list['base_shipping_amount']), 'product_id': self.shipping_product.id}).id
                                #print ('delivery_id+++++create',delivery_id)
                            else:
                                delivery_id = delivery_id[0]
                                delivery_id.write({'fixed_price':float(saleorder_list['base_shipping_amount'])})
                                #print ("delivery_id+++++++++++",delivery_id.fixed_price)
                                delivery_id = delivery_id.id
                        else:
                            delivery_id = delivery_obj.search([('name','=','Free delivery charges')])
                            if not delivery_id:
                                delivery_id = delivery_obj.create({'name': str(saleorder_list['shipping_description']),'product_id': self.shipping_product.id}).id
                            else:
                                delivery_id = delivery_id[0].id
                        if partner_id:
                            saleordervals.update({
                                'partner_id': partner_id[0].id,
                                'partner_invoice_id':partner_invoice_id[0].id if len(partner_invoice_id) > 0 else partner_id[0].id, 
                                'partner_shipping_id':partner_ship_id[0].id if len(partner_ship_id) > 0 else partner_id[0].id,
                                'name':str(saleorder_list['increment_id']),
                                'mage_order_id':str(saleorder_list['increment_id']),
                                'magento_shop_id':self.id,
                                'order_status':str(saleorder_list['status']),
                                'date_order':saleorder_list['created_at'],
                                'order_date':saleorder_list['created_at'],
                                'entity_id': saleorder_list.get('entity_id') or False,
                                'ma_order_id':saleorder_list['items'][0]['order_id'],
                                'magento_order': True,
                                'payment_term_id':payment_term_id,
                                'payment_method':payment_id.id,
                                'carrier_id':delivery_id,
                            })

                            if self.warehouse_id:
                                saleordervals.update({'warehouse_id':self.warehouse_id.id})

                            if self.pricelist_id:
                                saleordervals.update({'pricelist_id':self.pricelist_id.id})
                            saleorder_id=self.env['sale.order'].create(saleordervals)
                            disc_tax_id = []
                            for each_result in saleorder_list['items']:
                                if each_result.get('product_type')=='configurable':
                                    continue
                                else :
                                    #print ("each_result++++++++++++",each_result)
                                    product_id = []
                                    orderlinevals={}
                                    product_ids=self.env['product.product'].search([('default_code','=',str(each_result['sku']))])
                                    print ("product_ids+++++++++++++++++",product_ids)
                                    if not product_ids:
                                        product_id=self.env['product.product'].create_simple_products_orders(self.magento_instance_id,headers,each_result['sku'],self,self.website_id,each_result['product_id'])
                                        print ("product_id++++++++++++++",product_id)
                                    else:
                                        product_id = product_ids
                                    print ("product_ids+_+_+_+_+_+_+_+",product_id)
                                    if not product_id:
                                        product_ids = self.env['product.product'].search([('default_code','=','deleted_product')])
                                        if not product_ids:
                                            product_id = self.env['product.product'].create({'name':'Product Removed or Deleted','default_code':'deleted_product'})
                                        else:
                                            product_id = product_ids
        #                            else:
        #                                product_ids=self.env['product.product'].search([('default_code','=',str(each_result['sku']))])
        #                                if not product_ids:
        #                                    product_id=self.env['product.product'].create_simple_products(self.magento_instance_id,headers,each_result['sku'],self,self.website_id)
        #                                else:
        #                                    product_id = product_ids
        #                        if product_id[0].default_code == 'RMPRD':
        #                            name = '[' +each_result['sku'] + '] ' +each_result['name']
        #                        else:
        #                            name = each_result['name']
                                if 'parent_item'in each_result:
                                    parent_item = each_result['parent_item']
                                    if 'base_price' in parent_item and  parent_item['base_price'] > 0:
                                        unit_price = parent_item['base_price']
                                else:
                                    unit_price = each_result['base_price']
                                print ("unit_price+_+_+_+_+_+__+_",unit_price)
                                orderlinevals = {
                                    'order_id' : saleorder_id.id,
                                    'product_uom_qty' : float(each_result['qty_ordered']),
                                    #'product_uom' :product_id[0].product_tmpl_id.uom_id.id,
                                    #   'name' : name,
                                    'price_unit' : float(unit_price) ,
                                    'product_id' : product_id[0].id,
                                    'order_item_id':str(each_result['item_id']),
                                    }
                                tax_id = []
                                print ("each_result.get('tax_percent')_+_+_+_+_+_+",each_result.get('tax_percent'))
                                
                                if each_result.get('tax_percent') != None:
                                    tax_id = self.getTaxesAccountID(each_result)
                                    print ("tax_id_)_)_)_)_)_)",tax_id)
                                    if tax_id:
                                        orderlinevals['tax_id'] = [(6, 0, tax_id)]
                                        print("sfddddddddfdssfdfd")
                                    else:
                                        orderlinevals['tax_id'] =[(6, 0, [])]
                                else:
                                    orderlinevals['tax_id'] =[(6, 0, [])]
                                print ("orderlinevals+_+_+_+_+_+",orderlinevals)
                                #print ("orderlinevals+++++++++++++++",orderlinevals,type(each_result['qty_ordered']),type(each_result['base_price']),type(each_result['item_id']))
                                self.env['sale.order.line'].create(orderlinevals)
                                disc_tax_id = tax_id
                            print ("saleorder_list['discount_amount']+_+_+_+_+_+__+_+",saleorder_list['discount_amount'])
                            if float(saleorder_list['discount_amount']) != 0.00 or 'discount_invoiced' in saleorder_list and float(saleorder_list['discount_invoiced']) != 0.00:
                                if not self.discount_product:
                                    raise UserError(_('Please Configure Discount Product'))
                                if float(saleorder_list['discount_amount']) > 0:
                                    discount = float(saleorder_list['discount_amount'])
                                else:
                                    discount = float(saleorder_list['discount_invoiced'])
                                prod_shipping_id = self.discount_product
                                discountorderlinevals = {
                                    'order_id' : saleorder_id.id,
                                    'product_uom_qty' : 1,
                                    'product_uom' : prod_shipping_id.product_tmpl_id.uom_id.id,
                                    'name' : prod_shipping_id.name,
                                    'price_unit' : discount,
                                    'product_id' : self.discount_product.id,
                                    'tax_id': [(6, 0, disc_tax_id)],
                                    } 
                                print ("discountorderlinevals_)_)_+_+_+_+_",discountorderlinevals)
                                self.env['sale.order.line'].create(discountorderlinevals)
                            print ("saleorder_id+++++++++++",saleorder_id.carrier_id)
                            print ("saleorder_id+++++++++++",saleorder_id.carrier_id.fixed_price)
                            #saleorder_id.get_delivery_price()
                            if saleorder_id.carrier_id.fixed_price > 0:
                                delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
                                                            'default_order_id': saleorder_id.id,
                                                            'default_carrier_id': saleorder_id.carrier_id.id
                                                    }))
                                print ("delivery_wizard|++++",delivery_wizard)
                                choose_delivery_carrier = delivery_wizard.save()
                                print ("choose_delivery_carrier++++++++++++",choose_delivery_carrier)
                                choose_delivery_carrier.button_confirm()
                            #saleorder_id.set_delivery_line()
                self.write({'magento_order_date':date.today(),'magento_order_date_to':date.today()})
            else:
                raise UserError(_('To Date cannot be before From Date'))
        return True
    

    def GuestCustomer(self, saleorder_list):
        PartnerObj = self.env['res.partner']
        partner_id = PartnerObj.search([('email', '=', saleorder_list['customer_email'])])
        print("partner_id+_+_+_+_+_+_+_+_+_guest customer", partner_id)
        if not partner_id:
            vals = {'name': saleorder_list['customer_firstname'] + ' ' + saleorder_list['customer_lastname'],
                    'email': saleorder_list['customer_email'],
                    }
            partner_id = PartnerObj.create(vals)
            self._cr.commit()
        print("partner_id+_+_+_+_+_+_+_+_+_guest customer", partner_id)
        return partner_id

    def GuestCustomerInvoice(self, cust_address, partner_id):
        partner_vals = {}
        PartnerObj = self.env['res.partner']
        partner_invoice_id = PartnerObj.search(
            [('parent_id', '=', partner_id.id), ('mag_address_id', '=', cust_address['entity_id'])])
        print("partner_invoice_id+__+_+_+_+_+_+_guest", partner_invoice_id)
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
        # print ("partner_invoice_id+++++++++guest+_+_+customer",partner_invoice_id)
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
#         if hasattr(each_result ,'tax_percent') and float(each_result['tax_percent']) > 0.0:
        amount = float(each_result['tax_percent'])
        acctax_ids = accounttax_obj.search([('type_tax_use', '=', 'sale'),('amount', '=', amount)])

        if not len(acctax_ids):
            accounttax_id = accounttax_obj.create({'name':'Sales Tax(' + str(each_result['tax_percent']) + '%) ','amount':amount,'type_tax_use':'sale'})
            accounttax_id = accounttax_id.id
        else:
            accounttax_id = acctax_ids[0].id
        print ("accounttax_id+++++++++++++++",accounttax_id,[accounttax_id])
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
        return partner_invoice_id


    
    def GtCreateMagentoInvoice(self):
        #try:
        account_invoice_obj = self.env['account.move']
        self.magento_instance_id.generate_token()
        token=self.magento_instance_id.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token
            }
        url=str(self.magento_instance_id.location)+"/rest/V1/invoices?searchCriteria[filterGroups][0][filters][0][field]=store_id& searchCriteria[filterGroups][0][filters][0][value]=%s& searchCriteria[filterGroups][0][filters][0][conditionType]=eq"%(self.store_id,)
        response = requests.request("GET",url, headers=headers)
        items=response.json().get("items")
        for invoice_list in items:
            #try:
            print ("invoice_list++++++++++++++",invoice_list)
            invoice_ids = account_invoice_obj.search([('mage_invoice_id','=',invoice_list['increment_id'])])
            if not invoice_ids: 
                sale_id=self.env['sale.order'].search([('ma_order_id','=',invoice_list['order_id'])])
                logger.error('sale_id---------------  %s', sale_id)
                if sale_id:
                    print ("If condition")
                    if not sale_id.invoice_ids and sale_id.picking_ids:
                        print ("second if condition")
                        sale_id.action_confirm()
                        sale_id._create_invoices()
                        print("sale_id.invoice_ids",sale_id.invoice_ids)
                        for invoice_id in sale_id.invoice_ids:
                            print("invoice_id",invoice_id)
                            # invoice_id.action_invoice_open()
                            if sale_id.payment_method:
                                journal_id = self.env['account.journal'].search([('name','=',sale_id.payment_method.name.lower()),('code','=',sale_id.payment_method.name[:4].lower())], limit=1)
                                if not journal_id:
                                    journal_id = self.env['account.journal'].create({'name':sale_id.payment_method.name.lower(),'type':'bank','code':sale_id.payment_method.name[:4].lower()})
                            else:
                                journal_id = self.env['account.journal'].search([('name','=','default Magento payment'),('code','=','defau')], limit=1)
                                if not journal_id:
                                    journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                            # invoice_id.pay_and_reconcile(journal_id,invoice_id.amount_total)                                  
                            invoice_id.write({'mage_invoice_id':invoice_list['increment_id']})
                    else:
                        if not sale_id.invoice_ids:
                            print ("Else condition")
                            print ("sale confirm",sale_id[0].action_confirm())
                            print ("action invoice create",sale_id[0]._create_invoices())
                            for invoice_id in sale_id.invoice_ids:
                                #print ("invoice_id.account_id",invoice_id.account_id)
                                #print ("invoice open",invoice_id.action_invoice_open())
                                if len(sale_id.payment_method) > 0:
                                    journal_id = self.env['account.journal'].search([('name','=',sale_id.payment_method.name.lower()),('code','=',sale_id.payment_method.name[:4].lower())], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':sale_id.payment_method.name.lower(),'type':'bank','code':sale_id.payment_method.name[:4].lower()})
                                else:
                                    journal_id = self.env['account.journal'].search([('name','=','default Magento payment'),('code','=','defau')], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                #invoice_id.pay_and_reconcile(journal_id,invoice_id.amount_total)   
                                invoice_id.write({'mage_invoice_id':invoice_list['increment_id']})
                    print ("Invoiced True",sale_id.write({'invoiced': True}))
                    if sale_id.invoice_ids.state=='paid' and sale_id.picking_ids[0].state=='done' and sale_id.order_status=='complete':
                        sale_id.action_done()
                    self._cr.commit()

#                except Exception as exc:
#                    logger.error('Exception===================:  %s', exc)
#                   
#                    pass   
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            pass

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
        url=str(self.magento_instance_id.location)+"/rest/V1/shipments?searchCriteria[filterGroups][0][filters][0][field]=store_id& searchCriteria[filterGroups][0][filters][0][value]=%s& searchCriteria[filterGroups][0][filters][0][conditionType]=eq"%(self.store_id,)
        response = requests.request("GET",url, headers=headers)
        items=response.json().get("items")
        print ("items+++++++++++++++",items)
        print ("no of pick",len(items))
        if items:
            for shipment_list in items:
                #try:
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
#                except Exception as exc:
#                    logger.error('Exception===================:  %s', exc)
#                    pass 
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            pass
            
        return True
    
    
    
    def GtExportMagentoInvoice(self):
        try:
            shop_data = self
            account_invoice_obj = self.env['account.move']
            order_line_obj = self.env['sale.order.line']
            sale_obj = self.env['sale.order']
            shop_data.magento_instance_id.generate_token()
            token=shop_data.magento_instance_id.token
            headers = {
                'authorization':"Bearer "+token,
                'content-type': "application/json",
                'cache-control': "no-cache",
                }
            sale_ids = sale_obj.search([('magento_shop_id','=',self.id),('state','!=', 'sent'),'|',('order_status','=','pending'),('order_status','=','processing'),('invoiced','=',False)])
            if len(sale_ids) > 0:
                for sale_id in sale_ids:
                        # =============================here not getting the error================================
                    try:

                        invoice_id = account_invoice_obj.search([('invoice_origin','=',sale_id.name)])
                        for invoice in invoice_id:
                            if invoice.state=='cancel':
                                continue
                            item = []
        #                        order_line = order_line_obj.search([('product_id','=',line.product_id.id),('order_id','=',sale_id.id)])
                                #if order_line:
                            for order_line in  sale_id.order_line:
                                if order_line.product_id.type != 'service':
                                    item.append({"order_item_id":order_line.order_item_id,"qty":order_line.product_uom_qty,"extension_attributes": {}})
                            vals = {
                                    "capture": "true",
                                    "notify": "true",
                                    "appendComment": "true",
                                    "comment": {
                                      "extension_attributes": {},
                                      "comment": "string",
                                      "is_visible_on_front": 0
                                    },
                                    "arguments": {
                                      "extension_attributes": {}
                                    }
                                  }
                            payload = str(vals) 
                            payload=payload.replace("'",'"')  
                            payload=str(payload).replace('u"','"')
                            url=shop_data.magento_instance_id.location+"/rest/"+ str(sale_id.magento_shop_id.code) +"/V1/order/" + sale_id.entity_id +"/invoice"
                            response = requests.request("POST",url, data=payload, headers=headers)
                            if str(response.status_code)=="200":
                                each_response=json.loads(response.text)
                                if sale_id.shipped == True:
                                    sale_id.write({'invoiced': True,'order_status': 'complete'})
                                else:
                                    sale_id.write({'invoiced': True,'order_status': 'processing'})
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        pass   
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            pass
        return True
    
    
    
    
    def GtExportMagentoShipment(self):
        try:
            shop_data = self
            stock_obj = self.env['stock.picking']
            sale_obj = self.env['sale.order']
            shop_data.magento_instance_id.generate_token()
            token=shop_data.magento_instance_id.token
            headers = {
                'authorization':"Bearer "+token,
                'content-type': "application/json",
                'cache-control': "no-cache",
                }
            sale_ids = sale_obj.search([('magento_shop_id','=',self.id),'|',('order_status','=','pending'),('order_status','=','processing'),('shipped','=',False)])
            
            if len(sale_ids) > 0:
                for sale_id in sale_ids:
                    try:
                        stock_id = stock_obj.search([('origin','=',sale_id.name)])
                        logger.error('Stock_id==================  %s', stock_id)
                        if stock_id:
                            item = []
                            for line in sale_id.order_line:
                                if line.name != 'Shipping Product':
                                    if line.product_id.type != 'service':
                                        item.append({"order_item_id":line.order_item_id,"qty":line.product_uom_qty,"extension_attributes": {},})
                            logger.error('item==================  %s', item)
                            vals = {
                                "items": item,
                                "notify": "true",
                                "appendComment": "true",
                                    "comment": {
                                      "extension_attributes": {},
                                      "comment": "string",
                                      "is_visible_on_front": 0
                                    },
                                    "packages": [
                                      { 
                                        "extension_attributes": {}
                                      }
                                    ],
                                    "arguments": {
                                      "extension_attributes": {}
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
                            logger.error('vals==================  %s', vals)
                            payload = str(vals) 
                            payload=payload.replace("'",'"')     
                            payload=str(payload).replace('u"','"')
                            url=shop_data.magento_instance_id.location+"rest/"+ str(sale_id.magento_shop_id.code) +"/V1/order/" + sale_id.entity_id +"/ship" 
                            logger.error('url==================  %s', url)
                            response = requests.request("POST",url, data=payload, headers=headers)
                            logger.error('response code==================  %s', response.status_code)
                            if str(response.status_code)=="200":
                                each_response=json.loads(response.text)
                                if sale_id.invoiced == True:
                                    sale_id.write({'shipped': True,'order_status': 'complete'})
                                else:
                                    sale_id.write({'shipped': True,'order_status': 'processing'})
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        pass   
        except Exception as exc:
            #logger.error('Exception===================:  %s', exc)
            pass
        return True
