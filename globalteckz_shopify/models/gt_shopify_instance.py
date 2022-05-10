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


from odoo import fields,api,models, _
import requests
import json
import datetime
import base64
import urllib
import math
from datetime import date
import logging
logger = logging.getLogger('product')
import urllib.request
from odoo.exceptions import UserError

class GTShopifyInstance(models.Model):
    _name='gt.shopify.instance'
    _rec_name = 'gt_name'
    _description = "The Shopify Instance"
    
    gt_name = fields.Char(string='Instance Name',size=64, required=True)
    gt_location = fields.Char(string='Location',size=64,required=True)
    gt_api_key = fields.Char(string='Api Key',size=64,required=True)
    gt_password = fields.Char(string='password',size=64,required=True)
    gt_worflow_id = fields.Many2one('gt.import.order.workflow', string='Workflow & Settings')
    count_shopify_shop = fields.Integer(compute='get_shopify_shop_count')
    count_shopify_orders = fields.Integer(compute='get_shopify_orders_count')
    count_shopify_customers = fields.Integer(compute='get_shopify_customers_count')
    count_shopify_template = fields.Integer(compute='get_shopify_template_count')
    count_shopify_variant = fields.Integer(compute='get_shopify_variant_count')
    gt_financial_status = fields.Selection([('authorized', 'Authorized '),
                                        ('pending', 'Pending'),
                                        ('paid', 'Paid'),
                                        ('partially_paid', 'Partially Paid'),
                                        ('refunded', 'Refunded'),
                                        ('voided', 'Voided'),
                                        ('partially_refunded', 'Partially Refunded'),
                                        ('any', 'Any'),
                                        ('unpaid', 'Unpaid'),
                                      ], string="Financial Status", required=True, default='any')
    gt_status = fields.Selection([('open', 'Open '),
                                        ('closed', 'Closed'),
                                        ('cancelled', 'Cancelled'),
                                        ('any', 'Any'),
                                      ], string="Status", required=True, default='any')
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env['res.company']._company_default_get('gt.shopify.instance'))
    import_order_date = fields.Date(string='Import Order Date')
    export_stock_location = fields.Many2one('stock.location','Export Stock Location')
    
    
    
    
    def get_shopify_template_count(self):
        templ_obj = self.env['product.template']
        res = {}
        for shop in self:
            multishop_ids = templ_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_template = len(multishop_ids.ids)
        return res
    
    
    
    def get_shopify_variant_count(self):
        prod_obj = self.env['product.product']
        res = {}
        for shop in self:
            multishop_ids = prod_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_variant   = len(multishop_ids.ids)
        return res
    
    
    
    def get_shopify_shop_count(self):
        shop_obj = self.env['gt.shopify.store']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_shop = len(multishop_ids.ids)
        return res
    
    
    def get_shopify_orders_count(self):
        order_obj = self.env['sale.order']
        res = {}
        for shop in self:
            multishop_ids = order_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_orders = len(multishop_ids.ids)
        return res
    
    
    
    def get_shopify_customers_count(self):
        order_obj = self.env['res.partner']
        res = {}
        for shop in self:
            multishop_ids = order_obj.search([('gt_shopify_instance_id', '=', shop.id)])
            shop.count_shopify_customers = len(multishop_ids.ids)
        return res

    
    def gt_create_shopify_store(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Create Shopify Store','description': 'Successfull','gt_shopify_instance_id': self.id})
        store_obj = self.env['gt.shopify.store']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            shop_url = shopify_url + 'admin/shop.json'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            print ("response++++++++++++",response)
            store_dic=json.loads(response.text)
            print ("store_dic++++++++",store_dic)
            stores = store_dic['shop']
            print ("stores+++++++++++++",stores)
            vals = {
                'gt_store_name':stores['name'] if 'name' in stores else '',
                'gt_store_province':stores['province'] if 'province' in stores else '',
                'gt_store_province_code':stores['province_code'] if 'province_code' in stores else '',
                'gt_store_address1':stores['address1'] if 'address1' in stores else '',
                'gt_store_address2':stores['address2'] if 'address2' in stores else '',
                'gt_store_domain':stores['domain'] if 'domain' in stores else '',
                'gt_store_country_code':stores['country_code'] if 'country_code' in stores else '',
                'gt_store_zipcode':stores['zip'] if 'zip' in stores else '',
                'gt_store_city':stores['city'] if 'city' in stores else '',
                'gt_store_id':stores['id'] if 'id' in stores else '',
                'gt_store_currency':stores['currency'] if 'currency' in stores else '',
                'gt_store_email':stores['email'] if 'email' in stores else '',
                'gt_store_weight_unit':stores['weight_unit'] if 'weight_unit' in stores else '',
                'gt_store_country_name':stores['country_name'] if 'country_name' in stores else '',
                'gt_store_shop_owner':stores['shop_owner'] if 'shop_owner' in stores else '',
                'gt_store_plan_display_name':stores['plan_display_name'] if 'plan_display_name' in stores else '',
                'gt_store_phone':stores['phone'] if 'phone' in stores else '',
                'gt_shopify_instance_id': self.id,
            }
            stores_id = store_obj.search([('gt_store_id','=',stores['id'])])
            if len(stores_id) > 0:
                stores_id.write(vals)
            else:
                store_obj.create(vals)
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_line_obj.create({'name':'Create Shopify Store','description':exc,'create_date':date.today(),
                                      'shopify_log_id':log_id.id})
            log_id.write({'description': 'Something went wrong'}) 

        return True
    
    
    
    def gt_create_shopify_carrier_service(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Create Shopify Store','description': 'Successfull','gt_shopify_instance_id': self.id})
        carrier_obj = self.env['delivery.carrier']
        product_obj = self.env['product.product']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            carrier_url = shopify_url + '/admin/carrier_services.json'
            response = requests.get( carrier_url,auth=(api_key,api_pass))
            carrier_dic=json.loads(response.text)
            print ("carrier_url+++++++++",carrier_dic)
            carriers = carrier_dic['carrier_services']
            for carrier in carriers:
                product_id = product_obj.search([('default_code','=',carrier['name'])])
                if not product_id:
                    product_id = product_obj.create({'name':carrier['name'],'default_code':carrier['name'],'type':'service'})
                vals = {
                    'name':carrier['name'] if 'name' in carrier else '',
                    'gt_shopify_active':carrier['active'] if 'active' in carrier else '',
                    'gt_shopify_carrier_service_type':carrier['carrier_service_type'] if 'carrier_service_type' in carrier else '',
                    'gt_shopify_carrier_id':carrier['id'] if 'id' in carrier else '',
                    'gt_shopify_service_discovery':carrier['service_discovery'] if 'service_discovery' in carrier else '',
                    'gt_shopify_carrier':True,
                    'gt_shopify_instance_id':self.id,
                    'product_id':product_id.id,

                }
                carrier_id = carrier_obj.search([('gt_shopify_carrier_id','=',carrier['id']),('gt_shopify_instance_id','=',self.id)])
                if not carrier_id:
                    carrier_id = carrier_obj.create(vals)
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_line_obj.create({'name':'Create Shopify Store','description':exc,'create_date':date.today(),
                                      'shopify_log_id':log_id.id})
            #log_id.write({'description': 'Something went wrong'}) 

        return True
    
    
    
    def gt_create_shopify_location(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Create Shopify Location','description': 'Successfull','gt_shopify_instance_id': self.id})
        location_obj = self.env['stock.location']
        warehouse_obj = self.env['stock.warehouse']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        shop_url = shopify_url + 'admin/locations.json'
        response = requests.get( shop_url,auth=(api_key,api_pass))
        dic=json.loads(response.text)
        locations = dic['locations']
        for location in locations:
            warehouse_id = warehouse_obj.search([('code','=','shpfy')])
            if not warehouse_id:
                warehouse_id = warehouse_obj.create({'name': 'Shopify','code':'shpfy'})
            print ("warehouse_id++++++++",warehouse_id)
            vals = {
                'gt_shopify_location':True,
                'gt_shopify_location_id':location['id'] if 'id' in location else '',
                'name':location['name'] if 'name' in location else '',
                'location_id': 11,
            }
            print ('Vasl+++++++',vals)
            location_id = location_obj.search([('gt_shopify_location_id','=',location['id'])])
            print ('location_id++searc',location_id)
            if location_id:
                #print 'writing id'
                location_id.write(vals)
            else:
                location_id = location_obj.create(vals)
            warehouse_id.write({'lot_stock_id':location_id.id})
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_line_obj.create({'name':'Create Shopify Location','description':exc,'create_date':date.today(),
#                                      'shopify_log_id':log_id.id})
#            log_id.write({'description': 'Something went wrong'}) 

        return True
    
    
    
    def gt_import_shopify_products(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        count_url = shopify_url + '/admin/products/count.json'
        count_response = requests.get( count_url,auth=(api_key,api_pass))
        print ("count_response++++++++++",count_response)
        count_rs = json.loads(count_response.text)
        print ("count_rs+++++++++++++",count_rs)
        number_page =  count_rs['count'] / 50
        print ("number_page++++++++++0",number_page)
        number_page = int(round(number_page)) + 2
        print("number_page=======>>>",number_page)
        actual_page = []
        for k in range(int(number_page)):
            actual_page.append(k)
        actual_page.remove(0)
        print ("actual++++++++",actual_page)
        for page in actual_page:
            print ("page++++++++++++++",page)
            shop_url = shopify_url + 'admin/products.json?page='+str(page)
            print ("shop_url++++++",shop_url)
            response = requests.get( shop_url,auth=(api_key,api_pass))
            product_rs=json.loads(response.text)
            product_items = product_rs['products']
            print ("======",len(product_items))
            for products in product_items:
                product_tmpl_obj.gt_create_product_template(products,self,log_id)
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    def get_single_products(self,product_id):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        print ("product_id++++++++++++++",product_id)
        shop_url = shopify_url + 'admin/products/'+product_id+'.json'
        response = requests.get( shop_url,auth=(api_key,api_pass))
        print ("response++++++++++",response)
        product_rs=json.loads(response.text)
        print ("product_rs++++++++",product_rs)
        product_items = product_rs['product']
        print ("======",len(product_items))
        #for products in product_items:
        product_tmpl_obj.gt_create_product_template(product_items,self,log_id)
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
                
    
    def gt_export_shopify_products(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = product_tmpl_obj.search([('gt_shopify_exported','=', False),('gt_shopify_product','=',True)])
        ids = product_tmpl_obj.search([('id','=', 7)])
        ids.write({'gt_shopify_exported':True})
        print ("product_ids++++++++++++++++",product_ids)
        self._cr.commit()
        if product_ids:
            for products in product_ids:
                print (products)
                tag = ''
                print ("len(products.gt_product_tags)+++++++++++++++",len(products.gt_product_tags))
                if len(products.gt_product_tags) == 1:
                    tag = str(products.gt_product_tags.name)
                else:
                    for tags in products.gt_product_tags:
                        print ("tags++++++++++++++",tags)
                        tag += str(tags.name)+',' 
                        print ("tag++++++++++++",tag)
                if len(products.product_variant_ids) == 1:
                    print ("one variant",products.product_variant_ids)
                    vals = {        
                        "product": {
                            "title":str(products.name),
                            "body_html":str(products.gt_shopify_description),
                            "vendor": str(products.gt_vendor.name),
                            "product_type": str(products.gt_shopify_product_type.name),
                            "published_scope" : str(products.gt_published_scope.name),
                            "tags": tag,
                            "variants": [
                                {
                                  "price": str(products.list_price),
                                  "sku": str(products.default_code),
                                  "inventory_policy": 'deny',
                                  "fulfillment_service": 'manual',
                                  "inventory_management": 'shopify',
                                  "taxable": str(True),
                                  "barcode": str(products.product_variant_ids.barcode) or '',
                                  "weight": str(products.weight),
                                  "weight_unit": str(products.product_variant_ids.uom_id.name),
                                  "requires_shipping": str(products.product_variant_ids.gt_requires_shipping),
                                }
                              ],
                        }
                    }
                else:
                    print ("multi variant",products.product_variant_ids)
                    list_variant = []
                    option1_list = []
                    option2_list = []
                    option3_list = []
                    attribute1 = ''
                    attribute2 = ''
                    attribute3 = ''
                    options = []
                    for atts in products.product_variant_ids[0]:
                        if len(atts.attribute_value_ids) == 1:
                            attribute1 = str(atts.attribute_value_ids[0].attribute_id.name)
                        elif len(atts.attribute_value_ids) == 2:
                            attribute1 = str(atts.attribute_value_ids[0].attribute_id.name)
                            attribute2 = str(atts.attribute_value_ids[1].attribute_id.name)
                        elif len(atts.attribute_value_ids) == 3:
                            attribute1 = str(atts.attribute_value_ids[0].attribute_id.name)
                            attribute2 = str(atts.attribute_value_ids[1].attribute_id.name)
                            attribute3 = str(atts.attribute_value_ids[2].attribute_id.name)
                    for variants in products.product_variant_ids:
                        print (variants)
                        option1 = ''
                        option2 = ''
                        option3 = ''
                        #if len(variants.attribute_value_ids) == 3:
                        for atts in variants.attribute_value_ids:
                            if attribute1 == str(atts.attribute_id.name):
                                option1 = str(atts.name)
                                if str(atts.name) not in option1_list:
                                    option1_list.append(option1)
                            elif attribute2 == str(atts.attribute_id.name):
                                option2 = str(atts.name)
                                if str(atts.name) not in option2_list:
                                    option2_list.append(option2)
                            elif attribute3 == str(atts.attribute_id.name):
                                option3 = str(atts.name)
                                if str(atts.name) not in option3_list:
                                    option3_list.append(option3)
                        vals_variant = {
                                "price": str(variants.lst_price),
                                "sku": str(variants.default_code),
                                "inventory_policy": 'deny',
                                "fulfillment_service": 'manual',
                                "inventory_management": 'shopify',
                                "taxable": str(True),
                                "barcode": str(variants.gt_product_barcode) or str(variants.barcode) or '',
                                "weight": str(variants.weight),
                                #"weight_unit": str(variants.uom_id.name),
                                "requires_shipping": str(variants.gt_requires_shipping),
                                "option1": option1,
                                "option2": option2,
                                "option3": option3,
                              }
                        list_variant.append(vals_variant)
                    if len(option1_list) > 0:
                        vals_option = {"name": attribute1,"position": 1,"values": option1_list}
                        options.append(vals_option)
                    if len(option2_list) > 0:
                        vals_option = { "name": attribute2,"position": 2,"values": option2_list}
                        options.append(vals_option)
                    if len(option3_list) > 0:
                        vals_option = {"name": attribute3,"position": 3,"values": option3_list}
                        options.append(vals_option)
                    vals = {
                        "product": {
                          "title": str(products.name),
                          "body_html": str(products.gt_shopify_description),
                          "vendor": str(products.gt_vendor.name),
                          "product_type": str(products.gt_shopify_product_type.name),
                          "published_scope" : str(products.gt_published_scope.name),
                          "tags": tag,
                          "variants": list_variant,
                          "options": options,
                        }
                      }
                print ("vals++++++++++++++++++",vals)
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                print (payload)   
                shop_url = shopify_url + 'admin/products.json'
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)  
                product = product_rs['product']
                print ("product_rs+++++++++++++",product_rs)
                print (response)
                print ("type of response",type(response))
                #print "response code",response.code
                #logger.error('Exception===================:response', response)
                if str(response) == '<Response [201]>':
                    products.write({'gt_shopify_exported': True,'gt_product_id':product['id']})
                    for variant_id in product['variants']:
                        if 'sku' in variant_id:
                            product_id = product_obj.search([('default_code','=',variant_id['sku'])])
                            if product_id:
                                product_id.write({'gt_product_id':variant_id['id'],'gt_shopify_exported': True})
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    
    def gt_export_shopify_stock(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = product_obj.search([('gt_shopify_exported','=', True),('gt_shopify_product','=',True)])
        quant_obj = self.env['stock.quant']
        location_obj = self.env['stock.location']
        print ("product_ids+++++++++++++",product_ids)
        print ("length of product ids+++",len(product_ids))
        if product_ids:
            for products in product_ids:
                location_ids = location_obj.search([('gt_shopify_location','=',True)])
                for location_id in location_ids:
                    print (location_id)
                    quant_ids = quant_obj.search([('gt_shopify_exported','=',False),('product_id','=',products.id),('location_id','=',location_id.id)])
                    for quant_id in quant_ids:
                        print (quant_id)
                        vals = {
                            "location_id": str(location_id.gt_shopify_location_id),
                            "inventory_item_id": str(products.gt_inventory_item_id),
                            "available_adjustment": int(quant_id.qty),
                          }
                        payload=str(vals)
                        payload=payload.replace("'",'"')
                        payload=str(payload)
                        print( payload  ) 
                        shop_url = shopify_url + 'admin/inventory_levels/adjust.json'
                        print ("shop_url+++++++++++++",shop_url)
                        response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                        product_rs=json.loads(response.text)    
                        print ("product_rs+++++++++++++",product_rs)
                        print (response)
                        if str(response) == '<Response [200]>':
                            quant_id.write({'gt_shopify_exported':True})
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
        
    
    def gt_import_shopify_stock(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Inventory','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_obj = self.env['product.product']
        stock_inve_line_obj=self.env['stock.inventory.line']
        stock_inv_obj=self.env['stock.inventory']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        count_url = shopify_url + '/admin/products/count.json'
        count_response = requests.get( count_url,auth=(api_key,api_pass))
        count_rs = json.loads(count_response.text)
        print ("count_rs+++++++++++++",count_rs)
        number_page =  count_rs['count'] / 50
        print ("number_page++++++++++0",number_page)
        number_page = int(round(number_page)) + 2
        print("number_page=======>>>",number_page)
        actual_page = []
        for k in range(number_page):
            actual_page.append(k)
        actual_page.remove(0)
        print("actual_page====",actual_page)
        inventory_id = stock_inv_obj.create({'name':'update stock'+' '+str(datetime.datetime.now())})
        for page in actual_page:
            shop_url = shopify_url + 'admin/products.json?page=' +str(page)
            print("shop_url===>>>>>",shop_url)
            response = requests.get( shop_url,auth=(api_key,api_pass))
            product_rs=json.loads(response.text)
            product_items = product_rs['products']
            for products in product_items:
                #try:
                    if 'variants' in products:
                        for variant in products['variants']:
                            if 'sku' in variant:
                                if 'inventory_quantity' in variant:
                                    if int(variant['inventory_quantity']) > 0:
                                        print ("default_code+++++++++",variant['id'])
                                        product_id = product_obj.search([('gt_product_id','=',str(variant['id']))])
                                        print ("product_id++++++++++++++0",product_id)
                                        if product_id:
                                            print ("create inventory line ",stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':15,'product_id':product_id.id,'product_qty':int(variant['inventory_quantity'])}))
#                except Exception as exc:
#                    logger.error('Exception===================:  %s', exc)
#                    log_line_obj.create({'name':'Create Inventory','description':exc,'create_date':date.today(),
#                                              'shopify_log_id':log_id.id})
#                    log_id.write({'description': 'Something went wrong'}) 
        inventory_id._action_done()
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    def gt_import_shopify_image(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        photo_obj = self.env['gt.product.photo']
        try:
            shopify_url = str(self.gt_location)
            api_key = str(self.gt_api_key)
            api_pass = str(self.gt_password)
            product_ids = product_tmpl_obj.search([('gt_shopify_product','=',True),('gt_shopify_instance_id','=',self.id),('gt_product_id','!=', False)])
            for products in product_ids:
                print ("Shopify Product ID getting Images",products.gt_product_id)
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_id)+'/images.json'
                response = requests.get( shop_url,auth=(api_key,api_pass))
                product_rs=json.loads(response.text)
                product_items = product_rs['images']
                for image in product_items:
                    image_path = ""
                    try:
                        if len(image['variant_ids']) == 0:
                            print ("Creating Image---------------",image)
                            file_data = urllib.request.urlopen(image['src']).read()
                            image_path = base64.encodestring(file_data)
                            vals = {
                                'gt_image_src': image['src'] if 'src' in image else '',
                                'gt_image_id' : image['id'] if 'id' in image else '',
                                'gt_is_exported' : True,
                                'gt_image': image_path,
                                'gt_image_position' : image['position'] if 'position' in image else 0,
                                'gt_product_temp_id': products.id,
                                }
                            photo_id = photo_obj.search([('gt_image_id','=',image['id']),('gt_product_temp_id','=',products.id)])
                            if photo_id:
                                photo_id.write(vals)
                            else:
                                photo_obj.create(vals)
                            image_id = products.write({'image_medium':image_path})
                        else:
                            for product_ids in image['variant_ids']:
                                product_id = product_obj.search([('gt_product_id','=',product_ids)])
                                if product_id:
                                    print ("Creating Image----------",image)
                                    file_data = urllib.request.urlopen(image['src']).read()
                                    image_path = base64.encodestring(file_data)
                                    vals = {
                                        'gt_image_src': image['src'] if 'src' in image else '',
                                        'gt_image_id' : image['id']  if 'id' in image else '',
                                        'gt_is_exported' : True,
                                        'gt_image': image_path,
                                        'gt_image_position' : image['position'] if 'position' in image else 0,
                                        'gt_product_id': product_id.id,
                                        }
                                    photo_id = photo_obj.search([('gt_image_id','=',image['id']),('gt_product_id','=',product_id.id)])
                                    if photo_id:
                                        photo_id.write(vals)
                                    else:
                                        photo_obj.create(vals)
                                if image_path:
                                    variant_id = product_id.write({'image_medium':image_path})
                        self._cr.commit()
                        logger.error('Successfull product import  %s', products.name)
                    except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        log_line_obj.create({'name':'Create Image','description':exc,'create_date':date.today(),
                                                  'shopify_log_id':log_id.id})
                        log_id.write({'description': 'Something went wrong'}) 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            log_id.write({'description': exc}) 
        return True 
    
    
    
    
    def gt_export_shopify_image(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        photo_obj = self.env['gt.product.photo']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        product_ids = photo_obj.search([('gt_is_exported','=',False),('gt_shopify_instance_id','=',self.id)])
        for products in product_ids:
            print ("template before condition",products.gt_product_temp_id)
            print ("Product before condition",products.gt_product_id)
            if products.gt_product_temp_id:
                decodes = products.gt_image.decode("base64")
                newdecode = decodes.encode("base64")
                print ("Shopify Product Photo template ID",products.gt_product_temp_id)
                print ("template name",products.gt_product_temp_id.name)
                vals = {
                    "image": {
                      "position": products.gt_image_position,
                      "attachment": newdecode, 
                      "filename": str(products.gt_image_name),
                    }
                  }
                print ("vals++++++++++++++++++",vals)
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                print (payload)
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_temp_id.gt_product_id)+'/images.json'
                print ("shop_url++++++++++",shop_url)
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload, headers={'Content-Type': 'application/json',})
                print ("products+++++++++++++++",response)
                product_rs=json.loads(response.text)
                print ("product_rs+++++++++++++",product_rs)
                if str(response) == '<Response [200]>':
                    image =  product_rs['image']
                    print ("image+++++++++",image)
                    print ("writing image photo",products.write({'gt_is_exported': True,'gt_image_id':image['id'],'gt_image_src':image['src'],'gt_image_position':image['position']}))
                
            if products.gt_product_id:
                decodes = products.gt_image.decode("base64")
                newdecode = decodes.encode("base64")
                print ("Shopify Product Photo template ID",products.gt_product_temp_id)
                print ("template name",products.gt_product_temp_id.name)
                vals = {
                    "image": {
                      "variant_ids": [str(products.gt_product_id.gt_product_id)],
                      "position": products.gt_image_position,
                      "attachment": newdecode, 
                      "filename": str(products.gt_image_name),
                    }
                  }
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_id.product_tmpl_id.gt_product_id)+'/images.json'
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload, headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)
                if str(response) == '<Response [200]>':
                    image =  product_rs['image']
                    print ("image+++++++++",image)
                    print ("writing image photo",products.write({'gt_is_exported': True,'gt_image_id':image['id'],'gt_image_src':image['src'],'gt_image_position':image['position']}))
                
#                    except Exception, exc:
#                        logger.error('Exception===================:  %s', exc)
#                        log_line_obj.create({'name':'Create Image','description':exc,'create_date':date.today(),
#                                                  'shopify_log_id':log_id.id})
#                        log_id.write({'description': 'Something went wrong'}) 
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True 
    
    
    
    def gt_import_shopify_customers(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Customers','description': 'Successfull','gt_shopify_instance_id': self.id})
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        count_url = shopify_url + '/admin/customers/count.json'
        count_response = requests.get( count_url,auth=(api_key,api_pass))
        count_rs = json.loads(count_response.text)
        print ("count_rs+++++++++++++",count_rs)
        number_page =  count_rs['count'] / 50
        print ("number_page++++++++++0",number_page)
        number_page = int(round(number_page)) + 2
        print("number_page=======>>>",number_page)
        actual_page = []
        for k in range(number_page):
            actual_page.append(k)
        actual_page.remove(0)
        print ("actual++++++++",actual_page)
        for page in actual_page:
            print ("page++++++++++++++",page)
            shop_url = shopify_url + 'admin/customers.json?page='+str(page)
            print ("shop_url++++++",shop_url)
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['customers']
            print (len(items))
            for customer in items:
                self.create_customer(customer) 
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    
    def create_customer(self,customer):
        res_obj = self.env['res.partner']
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']
        status_id = []
        state_id = []
        country_id = []
        address1 = ''
        address2 = ''
        city = ''
        zip_code = ''
        name = ''
       # try:
        res_id = res_obj.search([('gt_customer_id','=', customer['id'])])
        if not res_id:
            if  'first_name' in customer:
                name = str(customer['first_name'])
            if 'last_name' in customer:
                name = str(customer['first_name']) + ' ' +str(customer['last_name'])
            if 'state' in customer:
                status = shopify_state_obj.search([('name','=',str(customer['state']))])
                if status:
                    status_id = status.id
                else:
                    status_id = shopify_state_obj.create({'name': str(customer['state'])}).id
            if 'default_address' in customer:
                address = customer['default_address']
                if 'address1' in address:
                   address1 = address['address1'] 
                if 'address2' in address:
                    address2 = address['address2']
                if 'city' in address:
                    city = address['city']
                if 'zip' in address:
                    zip_code = address['zip']
                print ("address['country_code']++++++++++",address['country_code'])
                print ("address['country_code']++++++++++type",type(address['country_code']))
                if str(address['country_code']) != 'None':
                    print ('condition satisfied')
                    country = res_country_obj.search([('code','=',str(address['country_code']))])
                    print ("country+++++++++++++",country)
                    print ("address['country_code']++++++++",address['country_code'])
                    print ("address['country_name']++++++++",address['country_name'])
                    if country:
                        country_id = country.id
                        print ("country++++++++++++ if",country_id)
                    else:
                        country_id = res_country_obj.create({'name': str(address['country_name']),'code': str(address['country_code']) if 'country_code' in address else ''}).id
                        print ("country++++++++++++    else",country_id)
                if str(address['province_code']) != 'None' and country_id:
                    print ("address['province']+++++++++++++",address['province'])
                    print ("address['province_code']++++++++",address['province_code'])
                    state = res_state_obj.search([('code','=',str(address['province_code'])),('country_id','=',country_id)])
                    print ("state+++++++++++",state)
                    if state:
                        state_id = state.id
                        print ("state_id+++++++++  if ",state_id)
                    else:
                        state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id
                        print ("state_id+++++++++  else ",state_id)
            vals = {
                'gt_customer_note': customer['note']if 'note' in customer else '',
                'gt_tax_exempt': customer['tax_exempt'] if 'tax_exempt' in customer else False,
                'gt_customer_id': customer['id'] if 'id' in customer else '',
                'gt_shopify_customer': True,
                'email': customer['email'] if 'email' in customer else '',
                'phone': customer['phone'] if 'phone' in customer else '',
                'gt_customer_state' : status_id,
                'country_id': country_id,
                'state_id': state_id,
                'street': address1,
                'street2':address2,
                'city': city,
                'zip': zip_code,
                'name': name,
                'gt_default_country_id': country_id,
                'gt_default_state_id': state_id,
                'gt_default_street': address1,
                'gt_default_street2':address2,
                'gt_default_city': city,
                'gt_default_zip': zip_code,
                'gt_default_name': name,
                'gt_shopify_instance_id' : self.id
            }


            ress = res_obj.create(vals)
            self._cr.commit()
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_line_obj.create({'name':'Create Customer','description':exc,'create_date':date.today(),
#                                      'shopify_log_id':log_id.id})
#            log_id.write({'description': 'Something went wrong'})
    
        return ress
    
    
    
    def gt_import_shopify_orders(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Orders','description': 'Successfull','gt_shopify_instance_id': self.id})
        res_obj = self.env['res.partner']
        sale_obj = self.env['sale.order']
        prod_obj = self.env['product.product']
        tax_obj = self.env['account.tax']
        payment_obj = self.env['account.payment.term']
        delivery_obj = self.env['delivery.carrier']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        count_url = shopify_url + '/admin/orders/count.json?status='+self.gt_status + '&financial_status='+self.gt_financial_status + '&created_at_min='+ str(self.import_order_date)+' 00:01:00'
        count_response = requests.get(count_url,auth=(api_key,api_pass))
        count_rs = json.loads(count_response.text)
        print ("count_rs+++++++++",count_rs)
        number_page =  count_rs['count'] / 50
        print ("number_page++++++++++0",number_page)
        number_page = int(round(number_page)) + 2
        print("number_page=======>>>",number_page)
        actual_page = []
        for k in range(number_page):
            actual_page.append(k)
        actual_page.remove(0)
        for page in actual_page:
            shop_url = shopify_url + 'admin/orders.json?status=any&page='+str(page) + '&created_at_min='+ str(self.import_order_date)+' 00:01:00'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['orders']
            for order in items:
                print ("order['order_number']++++++++++++++",order['order_number'])
                payment_id = []
                order_confirm = []
                order_stauts_url = ''
                order_currency = ''
                tax_incl = ''
                financial_status=''
                ful_status=''
                delivery_id = []
                #try:
                payment = payment_obj.search([('name','=','Immediate Payment')])
                if payment:
                    payment_id = payment.id
                if 'confirmed' in order:
                    order_confirm = order['confirmed']
                if self.company_id:
                    company_id = self.company_id.id
                else:
                    company_id = []
                if 'currency' in order:
                    order_currency = order['currency']
                if 'order_status_url' in order:
                    order_stauts_url = order['order_status_url']
                if 'taxes_included' in order:
                    tax_incl = order['taxes_included']  
                if 'financial_status' in order:
                    financial_status = order['financial_status']
                if 'fulfillment_status' in order:
                    ful_status = order['fulfillment_status']
                if 'shipping_lines' in order:
                    print ("order['shipping_lines']++++++",order['shipping_lines'])
                    if len(order['shipping_lines']) > 0:
                        shipping_line = order['shipping_lines'][0]
#                        print ("order['shipping_lines']++++++",order['shipping_lines'])
#                        print ("float(shipping_line['price'])++++++++++++",float(shipping_line['price']))
                        if float(shipping_line['price']) > 0.0:
                            delivery_id = delivery_obj.search([('name','=',shipping_line['title'])])
                            #print ("delivery_id+++++++++++++",delivery_id)
                            if not delivery_id:
                                product_id = prod_obj.search([('default_code','=',shipping_line['title'])])
                                #print ("product_id+++++++++++++",product_id)
                                if not product_id:
                                    product_id = prod_obj.create({'name':shipping_line['title'],'default_code':shipping_line['title'],'type':'service'})
                                    print ("product_id++++++++++++++++",product_id)
                                delivery_id = delivery_obj.create({'gt_shopify_carrier_id':shipping_line['id'],'name':shipping_line['title'],'fixed_price':shipping_line['price'],'product_id':product_id.id}).id
                                #print ("delivery_id++++++++++++++++++++",delivery_id)
                            else:
                                delivery_id.write({'fixed_price':shipping_line['price']})
                                delivery_id = delivery_id.id
                                #print ("delivery_id++++++++++++++",delivery_id)
                #print ("delivery_id++++++++++++",delivery_id)
                if 'customer' in order:
                    print ("order['customer']+++++++++++++",order['customer'])
                    customer = order['customer']
                    cust_id = res_obj.search([('gt_customer_id','=', customer['id'])])
                    if cust_id:
                        customer_id = cust_id
                    else:
                        customer_id =  self.create_customer(customer)
                    if customer_id:
                        if 'shipping_address' in order:
                            shipping_address = order['shipping_address']
                            self.update_shipping_address(shipping_address,customer_id[0])
                            print (True)

                    if 'line_items' in order:
                        items = order['line_items']
                        product_lines = []
                        for lines in items:
                            #print ("lines+++++++++++++",lines['name'])
                            product_id = []
#                            print ("lines variant ID++++++++++++",lines['variant_id'])
#                            print ("lines['product_id']+++++++++",lines['product_id'])
                            if lines['variant_id'] != None:
                                product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                if product:
                                    product_id = product
                                    #print ('print ()++++++',product_id)
                            else:
                                if lines['product_id'] != None:
                                    #print ("calling product")
                                    self.get_single_products(lines['product_id'])
                                    self._cr.commit()
                                    if lines['variant_id'] != None:
                                        product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                        product_id = product
                                        #print ("+product_id+++",product_id)
                            if 'tax_lines' in lines:
                                ta_line = lines['tax_lines']
                                tax_list = []
                                for tax_line in ta_line: 
                                    tax_title = str(tax_line['title']) + ' ' +str(tax_line['rate'] *  100)
                                    tax = tax_obj.search([('name','=',tax_title),('amount','=',tax_line['rate'] * 100),('type_tax_use','=','sale')])
                                    if tax:
                                        tax_id = tax
                                    else:
                                        tax_id = tax_obj.create({'name':tax_title,'amount':tax_line['rate'] * 100,'type_tax_use':'sale'})
                                    tax_list.append(tax_id.id)
#                            print ("product_id++++++++++",product_id)
#                            print ('lines++++++++++quantity+++++++++',lines['quantity'])
                            if not product_id:
                                product_id = prod_obj.search([('name','=','Product Removed')])
                                #print ("product_ids++++++++++++++",product_id)
                                if not product_id:
                                    product_id = prod_obj.create({'name':'Product Removed','defualt_code':'product_altered_removed','type':'product'})
                                    #print ("product_id++++++++++++",product_id)
                            product_lines.append((0,0,{'product_id': product_id.id,'tax_id': [(6, 0,tax_list)],'price_unit':lines['price'],'product_uom_qty': lines['quantity'],}))
                
                    if float(order['total_discounts']) != 0.00:
                        if not self.gt_worflow_id.discount_product:
                            raise UserError(_('Please Configure Discount Product'))

                        prod_disc_id = self.gt_worflow_id.discount_product
                        product_lines.append((0,0,{'product_id': prod_disc_id.id,'tax_id': [(6, 0,[])],'price_unit':-float(order['total_discounts']),'product_uom_qty': 1,}))
                else:
                    #raise UserError(_("Order Without Customer cannot be created in odoo !"))
                    pass
                sale_id = sale_obj.search([('name','=',order['order_number']),('gt_shopify_order_id','=',order['id'])])
                if not sale_id:
                    sale_id = sale_obj.create({'name':order['order_number'],
                        'partner_id':customer_id[0].id, 
                        'order_line': product_lines, 
                        'gt_shopify_instance_id': self.id, 
                        'gt_shopify_order': True,
                        'payment_term_id':payment_id,
                        'gt_shopify_order_id': order['id'],
                        'gt_shopify_order_status_url':order_stauts_url,
                        'gt_shopify_order_confirmed':order_confirm,
                        'gt_shopify_order_currency':order_currency,
                        'gt_financial_status':financial_status,
                        'gt_fulfillment_status':ful_status,
                        'gt_shopify_tax_included':tax_incl,
                        'date_order':order['created_at'],
                        'company_id':company_id,
                        'carrier_id':delivery_id,})
                    
                    if self.gt_worflow_id:
                        if self.gt_worflow_id.warehouse_id:
                            sale_id.write({'warehouse_id':self.gt_worflow_id.warehouse_id.id})

                        if self.gt_worflow_id.pricelist_id:
                            sale_id.write({'pricelist_id':self.gt_worflow_id.pricelist_id.id})

                        if self.gt_worflow_id.company_id:
                            sale_id.write({'company_id':self.gt_worflow_id.company_id.id})

                    
                    
                    if sale_id.carrier_id:
                        sale_id.get_delivery_price()
                        sale_id.set_delivery_line()
                        self._cr.commit()
                        order_ship_line_id = self.env['sale.order.line'].search([('order_id','=',sale_id.id),('product_id','=',sale_id.carrier_id.product_id.id)])
                        if order_ship_line_id:
                            if 'shipping_lines' in order:
                                shipping_line = order['shipping_lines'][0]
                                if len(shipping_line['tax_lines']) > 0:
                                    ta_line = lines['tax_lines']
                                    tax_list = []
                                    for tax_line in ta_line: 
                                        tax_title = str(tax_line['title']) + ' ' +str(tax_line['rate'] *  100)
                                        tax = tax_obj.search([('name','=',tax_title),('amount','=',tax_line['rate'] * 100),('type_tax_use','=','sale')])
                                        if tax:
                                            tax_id = tax
                                        else:
                                            tax_id = tax_obj.create({'name':tax_title,'amount':tax_line['rate'] * 100,'type_tax_use':'sale'})
                                        tax_list.append(tax_id.id)
                                    order_ship_line_id.write({'tax_id': [(6, 0,tax_list)]})
                    
                    if self.gt_worflow_id:
                        #print ("Worflow+++++++++++++++++++++++++++++",True)
                        if self.gt_worflow_id.validate_order==True and self.gt_worflow_id.complete_shipment==True:
                            #print ("first option++++++++++++++++")
                            sale_id.action_confirm()
                            print ("sale_id.picking_ids+++++++++",sale_id.picking_ids)
                            self._cr.commit()
                            for picking_id in sale_id.picking_ids:
                                picking_id.action_confirm()
                                picking_id.button_validate()
                                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                                wiz.process()
                                self._cr.commit()
                        elif self.gt_worflow_id.validate_order==True:
                            #print ("secondt option++++++++++++++++")
                            vals = sale_id.action_confirm()
                            self._cr.commit()
                        elif self.gt_worflow_id.complete_shipment==True:
                            #print ("third option++++++++++++++++")
                            sale_id.action_confirm()
                            self._cr.commit()
                            for picking_id in sale_id.picking_ids:
                                picking_id.action_confirm()
                                picking_id.button_validate()
                                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                                wiz.process()
                            self._cr.commit()
                            
                            
                        if self.gt_worflow_id.validate_invoice==True and self.gt_worflow_id.register_payment==True:
                            #print ('invoice first option++++++++++++++++')
                            if not sale_id.invoice_ids:
                                sale_id.action_confirm()
                                invoice_id = sale_id.action_invoice_create()
                                for invoice_id in sale_id.invoice_ids:
                                    invoice_id.action_invoice_open()
                                    if len(order['payment_gateway_names']) > 0:
                                        journal_id = self.env['account.journal'].search([('name','=',order['payment_gateway_names'][0].lower()),('code','=',order['payment_gateway_names'][0][:4].lower())], limit=1)
                                        if not journal_id:
                                            journal_id = self.env['account.journal'].create({'name':order['payment_gateway_names'][0].lower(),'type':'bank','code':order['payment_gateway_names'][0][:4].lower()})
                                    else:
                                        journal_id = self.env['account.journal'].search([('name','=','default shopify payment'),('code','=','defau')], limit=1)
                                        if not journal_id:
                                            journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                    invoice_id.pay_and_reconcile(self.gt_worflow_id.sale_journal or journal_id,invoice_id.amount_total)
                                self._cr.commit()
                        elif self.gt_worflow_id.validate_invoice==True:
                            #print ('invoice second option++++++++++++++++')
                            if not sale_id.invoice_ids:
                                sale_id.action_confirm()
                                invoice_id = sale_id.action_invoice_create()
                                acc_id=self.env['account.invoice'].browse(invoice_id)
                                acc_id.is_magento_id=True
                                for invoice_id in sale_id.invoice_ids:
                                    invoice_id.action_invoice_open()
                        elif self.gt_worflow_id.register_payment==True:
                            #print ('invoice third option++++++++++++++++')
                            if not sale_id.invoice_ids:
                                sale_id.action_confirm()
                                invoice_id = sale_id.action_invoice_create()
                                for invoice_id in sale_id.invoice_ids:
                                    invoice_id.action_invoice_open()
                                    if invoice_id.state not in ['paid']and invoice_id.invoice_line_ids:
                                        invoice_id.action_invoice_open()
                                        if len(order['payment_gateway_names']) > 0:
                                            journal_id = self.env['account.journal'].search([('name','=',order['payment_gateway_names'][0].lower()),('code','=',order['payment_gateway_names'][0][:4].lower())], limit=1)
                                            if not journal_id:
                                                journal_id = self.env['account.journal'].create({'name':order['payment_gateway_names'][0].lower(),'type':'bank','code':order['payment_gateway_names'][0][:4].lower()})
                                        else:
                                            journal_id = self.env['account.journal'].search([('name','=','default shopify payment'),('code','=','defau')], limit=1)
                                            if not journal_id:
                                                journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                        invoice_id.pay_and_reconcile(self.gt_worflow_id.sale_journal or journal_id,invoice_id.amount_total)
                
#                    else:
                    if sale_id.state == 'draft':
                        if order['financial_status'] == 'paid':
                            print ("financial status paid")
                            sale_id.action_confirm()
                            sale_id.action_invoice_create()
                            for invoice_id in sale_id.invoice_ids:
                                invoice_id.action_invoice_open()
                                if len(order['payment_gateway_names']) > 0:
                                    journal_id = self.env['account.journal'].search([('name','=',order['payment_gateway_names'][0].lower()),('code','=',order['payment_gateway_names'][0][:4].lower())], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':order['payment_gateway_names'][0].lower(),'type':'bank','code':order['payment_gateway_names'][0][:4].lower()})
                                else:
                                    journal_id = self.env['account.journal'].search([('name','=','default shopify payment'),('code','=','defau')], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                invoice_id.pay_and_reconcile(journal_id, invoice_id.amount_total)
                                sale_id.write({'gt_shopify_invoiced':True})
                        if order['fulfillment_status'] == 'fulfilled':
                            try:
                                print ("fulfillment status fulfilled")
                                print ('action confirm',sale_id.action_confirm())
                                for picking_id in sale_id.picking_ids:
                                    picking_id.action_confirm()
                                    picking_id.button_validate()
                                    wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                                    wiz.process()
                                sale_id.write({'gt_shopify_deliverd':True})
                            except Exception as exc:
                                pass
                    
                self._cr.commit()
#                except Exception as exc:
#                    logger.error('Exception===================:  %s', exc)
#                    log_line_obj.create({'name':'Create Order','description':exc,'create_date':date.today(),
#                                              'shopify_log_id':log_id.id})
#                    log_id.write({'description': 'Something went wrong'}) 
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    def gt_import_shopify_orders_dashboard(self,date):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Orders','description': 'Successfull','gt_shopify_instance_id': self.id})
        res_obj = self.env['res.partner']
        sale_obj = self.env['sale.order']
        prod_obj = self.env['product.product']
        tax_obj = self.env['account.tax']
        payment_obj = self.env['account.payment.term']
        delivery_obj = self.env['delivery.carrier']
        #try:
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        count_url = shopify_url + '/admin/orders/count.json?status='+self.gt_status + '&financial_status='+self.gt_financial_status + '&created_at_min='+ str(date)+' 00:01:00'
        count_response = requests.get(count_url,auth=(api_key,api_pass))
        count_rs = json.loads(count_response.text)
        print ("count_rs+++++++++",count_rs)
        number_page =  count_rs['count'] / 50
        print ("number_page++++++++++0",number_page)
        number_page = int(round(number_page)) + 2
        print("number_page=======>>>",number_page)
        actual_page = []
        for k in range(number_page):
            actual_page.append(k)
        actual_page.remove(0)
        for page in actual_page:
            shop_url = shopify_url + 'admin/orders.json?status=any&page='+str(page) + '&created_at_min='+ str(date)+' 00:01:00'
            response = requests.get( shop_url,auth=(api_key,api_pass))
            customer_rs=json.loads(response.text)
            items = customer_rs['orders']
            for order in items:
                print ("order++++++++",order)
                payment_id = []
                order_confirm = []
                order_stauts_url = ''
                order_currency = ''
                tax_incl = ''
                financial_status=''
                ful_status=''
                #try:
                payment = payment_obj.search([('name','=','Immediate Payment')])
                if payment:
                    payment_id = payment.id
                if 'confirmed' in order:
                    order_confirm = order['confirmed']
                if self.company_id:
                    company_id = self.company_id.id
                else:
                    company_id = []
                print ("total_discounts++++++++++++++")
                print ("total_discounts++++++++++++++")
                print ("total_discounts++++++++++++++")
                print ("total_discounts++++++++++++++",order['total_discounts'])
                print ("total_discounts++++++++++++++",order['total_discounts'])
                print ("total_discounts++++++++++++++",order['total_discounts'])
                if 'currency' in order:
                    order_currency = order['currency']
                if 'order_status_url' in order:
                    order_stauts_url = order['order_status_url']
                if 'taxes_included' in order:
                    tax_incl = order['taxes_included']  
                if 'financial_status' in order:
                    financial_status = order['financial_status']
                if 'fulfillment_status' in order:
                    ful_status = order['fulfillment_status']
                if 'shipping_lines' in order:
                    print ("order['shipping_lines']++++++",order['shipping_lines'])
                    if len(order['shipping_lines']) > 0:
                        shipping_line = order['shipping_lines'][0]
                        print ("order['shipping_lines']++++++",order['shipping_lines'])
                        if float(shipping_line['price']) > 0.0:
                            delivery_id = delivery_obj.search([('name','=',shipping_line['title'])])
                            if not delivery_id:
                                product_id = prod_obj.search([('default_code','=',shipping_line['title'])])
                                if not product_id:
                                    product_id = prod_obj.create({'name':shipping_line['title'],'default_code':shipping_line['title'],'type':'service'})
                                delivery_id = delivery_obj.create({'gt_shopify_carrier_id':shipping_line['id'],'name':shipping_line['title'],'fixed_price':shipping_line['price'],'product_id':product_id.id}).id
                            else:
                                delivery_id.write({'fixed_price':shipping_line['price']})
                                delivery_id = delivery_id.id
                if 'customer' in order:
                    customer = order['customer']
                    print ("customer+++++++++++",customer)
                    cust_id = res_obj.search([('gt_customer_id','=', customer['id'])])
                    print ("customer_id++++++++",cust_id)
                    if cust_id:
                        customer_id = cust_id
                    else:
                        customer_id =  self.create_customer(customer)
                    print ("customer_id++++++++",customer_id)
                    if customer_id:
                        if 'shipping_address' in order:
                            shipping_address = order['shipping_address']
                            self.update_shipping_address(shipping_address,customer_id[0])
                            print (True)

                    if 'line_items' in order:
                        print ("order['line_items']+++++++++++",order['line_items'])
                        items = order['line_items']
                        product_lines = []
                        for lines in items:
                            product_id = []
                            print ("lines variant ID++++++++++++",lines['variant_id'])
                            print ("lines['product_id']+++++++++",lines['product_id'])
                            if lines['variant_id'] != None:
                                product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                if product:
                                    product_id = product
                                    print ('print ()++++++',product_id)
                            else:
                                if lines['product_id'] != None:
                                    print ("calling product")
                                    self.get_single_products(lines['product_id'])
                                    self._cr.commit()
                                    if lines['variant_id'] != None:
                                        product = prod_obj.search([('gt_product_id','=',lines['variant_id'])])
                                        product_id = product
                                        print ("+product_id+++",product_id)
                            if 'tax_lines' in lines:
                                ta_line = lines['tax_lines']
                                tax_list = []
                                for tax_line in ta_line: 
                                    tax_title = str(tax_line['title']) + ' ' +str(tax_line['rate'] *  100)
                                    tax = tax_obj.search([('name','=',tax_title),('amount','=',tax_line['rate'] * 100),('type_tax_use','=','sale')])
                                    if tax:
                                        tax_id = tax
                                    else:
                                        tax_id = tax_obj.create({'name':tax_title,'amount':tax_line['rate'] * 100,'type_tax_use':'sale'})
                                    tax_list.append(tax_id.id)
                            print ("product_id++++++++++",product_id)
                            print ('lines++++++++++quantity+++++++++',lines['quantity'])
                            if not product_id:
                                product_ids = prod_obj.search([('default_code','=','product_altered_removed')])
                                print ("product_ids++++++++++++++",product_ids)
                                if not product_ids:
                                    product_ids = prod_obj.create({'name':'Product Removed','defualt_code':'product_altered_removed'})
                            product_lines.append((0,0,{'product_id': product_ids.id,'tax_id': [(6, 0,tax_list)],'price_unit':lines['price'],'product_uom_qty': lines['quantity'],}))
                
                    if float(order['total_discounts']) != 0.00:
                        if not self.gt_worflow_id.discount_product:
                            raise UserError(_('Please Configure Discount Product'))

                        prod_disc_id = self.gt_worflow_id.discount_product
                        product_lines.append((0,0,{'product_id': prod_disc_id.id,'tax_id': [(6, 0,[])],'price_unit':-float(order['total_discounts']),'product_uom_qty': 1,}))
                else:
                    raise UserError(_("Order Without Customer cannot be created in odoo !"))
                sale_id = sale_obj.search([('name','=',order['order_number']),('gt_shopify_order_id','=',order['id'])])
                if not sale_id:
                    sale_id = sale_obj.create({'name':order['order_number'],
                        'partner_id':customer_id[0].id, 
                        'order_line': product_lines, 
                        'gt_shopify_instance_id': self.id, 
                        'gt_shopify_order': True,
                        'payment_term_id':payment_id,
                        'gt_shopify_order_id': order['id'],
                        'gt_shopify_order_status_url':order_stauts_url,
                        'gt_shopify_order_confirmed':order_confirm,
                        'gt_shopify_order_currency':order_currency,
                        'gt_financial_status':financial_status,
                        'gt_fulfillment_status':ful_status,
                        'gt_shopify_tax_included':tax_incl,
                        'date_order':order['created_at'],
                        'company_id':company_id,})
                    
                    if self.gt_worflow_id:
                        if self.gt_worflow_id.warehouse_id:
                            sale_id.write({'warehouse_id':self.gt_worflow_id.warehouse_id.id})

                        if self.gt_worflow_id.pricelist_id:
                            sale_id.write({'pricelist_id':self.gt_worflow_id.pricelist_id.id})

                        if self.gt_worflow_id.company_id:
                            sale_id.write({'company_id':self.gt_worflow_id.company_id.id})

                    
                    
                    if sale_id.carrier_id:
                        sale_id.get_delivery_price()
                        sale_id.set_delivery_line()
                        self._cr.commit()
                        order_ship_line_id = self.env['sale.order.line'].search([('order_id','=',sale_id.id),('product_id','=',sale_id.carrier_id.product_id.id)])
                        if order_ship_line_id:
                            if 'shipping_lines' in order:
                                shipping_line = order['shipping_lines'][0]
                                if len(shipping_line['tax_lines']) > 0:
                                    ta_line = lines['tax_lines']
                                    tax_list = []
                                    for tax_line in ta_line: 
                                        tax_title = str(tax_line['title']) + ' ' +str(tax_line['rate'] *  100)
                                        tax = tax_obj.search([('name','=',tax_title),('amount','=',tax_line['rate'] * 100),('type_tax_use','=','sale')])
                                        if tax:
                                            tax_id = tax
                                        else:
                                            tax_id = tax_obj.create({'name':tax_title,'amount':tax_line['rate'] * 100,'type_tax_use':'sale'})
                                        tax_list.append(tax_id.id)
                                    order_ship_line_id.write({'tax_id': [(6, 0,tax_list)]})
                    
                    if self.gt_worflow_id:
                        print ("Worflow+++++++++++++++++++++++++++++",True)
                        if self.gt_worflow_id.validate_order==True and self.gt_worflow_id.complete_shipment==True:
                            print ("first option++++++++++++++++")
                            sale_id.action_confirm()
                            print ("sale_id.picking_ids+++++++++",sale_id.picking_ids)
                            self._cr.commit()
                            for picking_id in sale_id.picking_ids:
                                picking_id.action_confirm()
                                picking_id.button_validate()
                                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                                wiz.process()
                                self._cr.commit()
                        elif self.gt_worflow_id.validate_order==True:
                            print ("secondt option++++++++++++++++")
                            vals = sale_id.action_confirm()
                            self._cr.commit()
                        elif self.gt_worflow_id.complete_shipment==True:
                            print ("third option++++++++++++++++")
                            sale_id.action_confirm()
                            self._cr.commit()
                            for picking_id in sale_id.picking_ids:
                                picking_id.action_confirm()
                                picking_id.button_validate()
                                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                                wiz.process()
                            self._cr.commit()
                            
                            
                        if self.gt_worflow_id.validate_invoice==True and self.gt_worflow_id.register_payment==True:
                            print ('invoice first option++++++++++++++++')
                            if not sale_id.invoice_ids:
                                sale_id.action_confirm()
                                invoice_id = sale_id.action_invoice_create()
                                for invoice_id in sale_id.invoice_ids:
                                    invoice_id.action_invoice_open()
                                    if len(order['payment_gateway_names']) > 0:
                                        journal_id = self.env['account.journal'].search([('name','=',order['payment_gateway_names'][0].lower()),('code','=',order['payment_gateway_names'][0][:4].lower())], limit=1)
                                        if not journal_id:
                                            journal_id = self.env['account.journal'].create({'name':order['payment_gateway_names'][0].lower(),'type':'bank','code':order['payment_gateway_names'][0][:4].lower()})
                                    else:
                                        journal_id = self.env['account.journal'].search([('name','=','default shopify payment'),('code','=','defau')], limit=1)
                                        if not journal_id:
                                            journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                    invoice_id.pay_and_reconcile(self.gt_worflow_id.sale_journal or journal_id,invoice_id.amount_total)
                                self._cr.commit()
                        elif self.gt_worflow_id.validate_invoice==True:
                            print ('invoice second option++++++++++++++++')
                            if not sale_id.invoice_ids:
                                sale_id.action_confirm()
                                invoice_id = sale_id.action_invoice_create()
                                acc_id=self.env['account.invoice'].browse(invoice_id)
                                acc_id.is_magento_id=True
                                for invoice_id in sale_id.invoice_ids:
                                    invoice_id.action_invoice_open()
                        elif self.gt_worflow_id.register_payment==True:
                            print ('invoice third option++++++++++++++++')
                            if not sale_id.invoice_ids:
                                sale_id.action_confirm()
                                invoice_id = sale_id.action_invoice_create()
                                for invoice_id in sale_id.invoice_ids:
                                    invoice_id.action_invoice_open()
                                    if invoice_id.state not in ['paid']and invoice_id.invoice_line_ids:
                                        invoice_id.action_invoice_open()
                                        if len(order['payment_gateway_names']) > 0:
                                            journal_id = self.env['account.journal'].search([('name','=',order['payment_gateway_names'][0].lower()),('code','=',order['payment_gateway_names'][0][:4].lower())], limit=1)
                                            if not journal_id:
                                                journal_id = self.env['account.journal'].create({'name':order['payment_gateway_names'][0].lower(),'type':'bank','code':order['payment_gateway_names'][0][:4].lower()})
                                        else:
                                            journal_id = self.env['account.journal'].search([('name','=','default shopify payment'),('code','=','defau')], limit=1)
                                            if not journal_id:
                                                journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                        invoice_id.pay_and_reconcile(self.gt_worflow_id.sale_journal or journal_id,invoice_id.amount_total)
                
#                    else:
                    if sale_id.state == 'draft':
                        if order['financial_status'] == 'paid':
                            print ("financial status paid")
                            sale_id.action_confirm()
                            sale_id.action_invoice_create()
                            for invoice_id in sale_id.invoice_ids:
                                invoice_id.action_invoice_open()
                                if len(order['payment_gateway_names']) > 0:
                                    journal_id = self.env['account.journal'].search([('name','=',order['payment_gateway_names'][0].lower()),('code','=',order['payment_gateway_names'][0][:4].lower())], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':order['payment_gateway_names'][0].lower(),'type':'bank','code':order['payment_gateway_names'][0][:4].lower()})
                                else:
                                    journal_id = self.env['account.journal'].search([('name','=','default shopify payment'),('code','=','defau')], limit=1)
                                    if not journal_id:
                                        journal_id = self.env['account.journal'].create({'name':'default shopify payment','type':'bank','code': 'defau'})
                                invoice_id.pay_and_reconcile(journal_id, invoice_id.amount_total)
                                sale_id.write({'gt_shopify_invoiced':True})
                        if order['fulfillment_status'] == 'fulfilled':
                            try:
                                print ("fulfillment status fulfilled")
                                print ('action confirm',sale_id.action_confirm())
                                for picking_id in sale_id.picking_ids:
                                    picking_id.action_confirm()
                                    picking_id.button_validate()
                                    wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_id.id)]})
                                    wiz.process()
                                sale_id.write({'gt_shopify_deliverd':True})
                            except Exception as exc:
                                pass
                    
                self._cr.commit()
#                except Exception as exc:
#                    logger.error('Exception===================:  %s', exc)
#                    log_line_obj.create({'name':'Create Order','description':exc,'create_date':date.today(),
#                                              'shopify_log_id':log_id.id})
#                    log_id.write({'description': 'Something went wrong'}) 
#        except Exception as exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
        
    
    
    def update_shipping_address(self,address,customer_id):
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']   
        country_id = []
        state_id = []
        if 'address1' in address:
            address1 = address['address1'] 
            if 'address2' in address:
                address2 = address['address2']
            if 'city' in address:
                city = address['city']
            if 'zip' in address:
                zip_code = address['zip']
            if address['country'] != None:
                country = res_country_obj.search([('name','=',str(address['country'])),('code','=',str(address['country_code']))])
                if country:
                    country_id = country.id
                else:
                    country_id = res_country_obj.create({'name': str(address['country']),'code': str(address['country_code']) if 'country_code' in address else ''}).id
            if address['province'] != None:
                state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                if state:
                    state_id = state.id
                else:
                    state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id
        customer_id.write({
            'country_id': country_id,
            'state_id': state_id,
            'street': address1,
            'street2':address2,
            'city': city,
            'zip': zip_code,
        })
        
        return True
        
    
    
    
    def create_order_customer(self,res_obj,customer): 
        shopify_state_obj = self.env['gt.shopify.customer.state']
        res_state_obj = self.env['res.country.state']
        res_country_obj = self.env['res.country']
        country_id = []
        state_id = []
        if  'first_name' in customer:
            name = str(customer['first_name'])
            if 'last_name' in customer:
                name = str(customer['first_name']) + ' ' +str(customer['last_name'])
            if 'state' in customer:
                status = shopify_state_obj.search([('name','=',str(customer['state']))])
                if status:
                    status_id = status.id
                else:
                    status_id = shopify_state_obj.create({'name': str(customer['state'])}).id
        if 'default_address' in customer:
            address = customer['default_address']
            if 'address1' in address:
               address1 = address['address1'] 
            if 'address2' in address:
                address2 = address['address2']
            if 'city' in address:
                city = address['city']
            if 'zip' in address:
                zip_code = address['zip']
            if address['country'] != None:
                country = res_country_obj.search([('name','=',str(address['country_name'])),('code','=',str(address['country_code']))])
                if country:
                    country_id = country.id
                else:
                    country_id = res_country_obj.create({'name': str(address['country_name']),'code': str(address['country_code']) if 'country_code' in address else ''}).id

            if address['province'] != None:
                state = res_state_obj.search([('name','=',str(address['province'])),('country_id','=',country_id)])
                if state:
                    state_id = state.id
                else:
                    state_id = res_state_obj.create({'name': str(address['province']),'country_id': country_id, 'code':str(address['province_code']) if 'province_code' in address else ''}).id
        customer_vals = {
            'name':name,
            'gt_customer_note': customer['note']if 'note' in customer else '',
            'gt_tax_exempt': customer['tax_exempt'] if 'tax_exempt' in customer else False,
            'gt_customer_id': customer['id'] if 'id' in customer else '',
            'gt_shopify_customer': True,
            'email': customer['email'] if 'email' in customer else '',
            'phone': customer['phone'] if 'phone' != None in customer else '',
            'gt_customer_state' : status_id,
            'gt_default_country_id': country_id,
            'gt_default_state_id': state_id,
            'gt_default_street': address1,
            'gt_default_street2':address2,
            'gt_default_city': city,
            'gt_default_zip': zip_code,
            'gt_default_name': name,
            'gt_shopify_instance_id': self.id}
        customer_id = res_obj.create(customer_vals)
        
        
        return customer_id
    
    
    
    
    def gt_export_shipment(self):
        sale_obj = self.env['sale.order']
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        #log_id = log_obj.create({'create_date':date.today(),'name': 'Create Shopify Store','description': 'Successfull','gt_shopify_instance_id': self.id})
        carrier_obj = self.env['delivery.carrier']
        product_obj = self.env['product.product']
        shopify_url = str(self.gt_location)
        api_key = str(self.gt_api_key)
        api_pass = str(self.gt_password)
        try:
            sale_ids = sale_obj.search([('gt_shopify_order','=',True),('gt_shopify_deliverd','=',False)])
            for sale_id in  sale_ids:
                if sale_id.picking_ids:
                    vals =  {
                   "fulfillment": {
                    "tracking_company": sale_id.picking_ids[0].carrier_id.name,
                    "tracking_number": sale_id.picking_ids[0].carrier_tracking_ref if sale_id.picking_ids[0].carrier_tracking_ref else '',
                    "notify_customer": 'True',
                   }
                   }
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                print (payload)
                #shop_url = shopify_url + 'admin/orders/'+str(sale_id.gt_shopify_order_id)+'/fulfillments.json'
                shop_url = shopify_url + 'admin/orders/316538191918/fulfillments.json'
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)    
                print ("product_rs+++++++++++++",product_rs)
                print (response)
                print ("type of response",type(response))
                #print "response code",response.code
                if str(response) == '<Response [201]>':
                    sale_id.write({'gt_shopify_deliverd': True})
            
            carrier_url = shopify_url + '/admin/carrier_services.json'
            response = requests.get( carrier_url,auth=(api_key,api_pass))
            carrier_dic=json.loads(response.text)
            carriers = carrier_dic['carrier_services']
            
           
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            #log_line_obj.create({'name':'Create Shopify Store','description':exc,'create_date':date.today(),
                                 #     'shopify_log_id':log_id.id})
            #log_id.write({'description': 'Something went wrong'}) 

        return True
    
    
    
    
    def action_get_shop(self):
        shopify_shop = self.env['gt.shopify.store'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.action_gt_shopify_store')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_shop.ids)]
        }
        return result
    
    
    
    def action_get_orders(self):
        shopify_orders = self.env['sale.order'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.action_orders_shopify_all')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_orders.ids)]
        }

        return result
    
    
    
    def action_get_customers(self):
        shopify_customers = self.env['res.partner'].search([('gt_shopify_instance_id','=',self.id),('gt_shopify_customer','=',True)])
        action = self.env.ref('globalteckz_shopify.action_shopify_customer')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_customers.ids)]
        }

        return result
    
    
    
    
    def action_get_product_template(self):
        shopify_templ = self.env['product.template'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.shopify_product_template_exported')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_templ.ids)]
        }

        return result
    
    
    
    
    def action_get_product_variant(self):
        shopify_prod = self.env['product.product'].search([('gt_shopify_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_shopify.shopify_products_variant_exported')
        result = {
        'name': action.name,
        'help': action.help,
        'type': action.type,
        'view_type': action.view_type,
        'view_mode': action.view_mode,
        'target': action.target,
        'context': action.context,
        'res_model': action.res_model,
        'domain': [('id', 'in', shopify_prod.ids)]
        }

        return result
