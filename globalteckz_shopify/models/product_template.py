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


from odoo import fields,api,models, tools
import itertools
import psycopg2
import logging
logger = logging.getLogger('product')
from datetime import date
import requests
import json
import base64


class ProductTemplate(models.Model):
    _inherit='product.template'
    
    
    gt_published_scope = fields.Many2one('gt.published.scope', string='Published Scope')
    gt_shopify_description = fields.Text(string='Shopify Description')
    gt_vendor = fields.Many2one('gt.shopify.vendor',string='Vendor')
    gt_product_id = fields.Char(string='Product ID')
    gt_requires_shipping = fields.Boolean(string='Requires Shipping')
    gt_product_tags = fields.Many2many('gt.shopify.product.tags', 'tags_product_rel', 'tags_id', 'tags', string='Product Tags')
    gt_shopify_product = fields.Boolean(string='Shopify Product')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_product_image_id = fields.One2many('gt.product.photo', 'gt_product_temp_id', string='Product Images')
    gt_shopify_exported = fields.Boolean(string='Shopify Exported')
    gt_shopify_product_type = fields.Many2one('gt.shopify.product.type',string='Shopify Product Type')
    
    
    
    def gt_create_product_template(self,products,instance,log_id):
        product_obj = self.env['product.product']
        scope_obj = self.env['gt.published.scope']
        vendor_obj = self.env['gt.shopify.vendor']
        tags_obj = self.env['gt.shopify.product.tags']
        product_attribute_obj = self.env['product.attribute']
        product_attribute_option_obj = self.env['product.attribute.value']
        product_type_obj = self.env['gt.shopify.product.type']
        log_line_obj = self.env['shopify.log.details']
        scopes = []
        vendors = []
        tags_lst = []
        type_id = []
       # try:
        if 'product_type' in products:
            product_type_id = product_type_obj.search([('name','=',products['product_type'])])
            if len(product_type_id) > 0 :
                type_id = product_type_id[0].id
            else:
                type_id = product_type_obj.create({'name': products['product_type'], 'gt_shopify_instance_id':instance.id }).id
        if 'title' in products:
            scope_id = scope_obj.search([('name','=',products['published_scope'])])
            if len(scope_id) > 0 :
               scopes =  scope_id[0].id
            else:
                scopes = scope_obj.create({'name':str(products['published_scope']),'gt_shopify_instance_id':instance.id}).id
        if 'vendor' in products:
            vendor_id = vendor_obj.search([('name','=',products['vendor'])])
            if vendor_id:
               vendors =  vendor_id[0].id
            else:
                vendors = vendor_obj.create({'name':str(products['vendor']),'gt_shopify_instance_id':instance.id}).id
        if instance.company_id:
            company_id = instance.company_id.id
        else:
            company_id = []
        if 'tags' in products:
            if str(products['tags']) != '':
                tags_split = products['tags'].split(',')
                for tags in tags_split:
                    tags_id = tags_obj.search([('name','=',str(tags))])
                    if len(tags_id) > 0:
                        tags_lst.append(tags_id[0].id)
                    else:
                        tags_id = tags_obj.create({'name':str(tags),'gt_shopify_instance_id':instance.id})
                        tags_lst.append(tags_id.id)
        variant = []
        for options in products['options']:
            if str(options['name']) != 'Title':
                attribute_id = []
                att_search = []
                value_search = []
                if 'name' in options:
                    att_name = str(options['name'])
                    att_id = product_attribute_obj.search([('name','=',att_name.lower())])
                    att_search.append(att_id.id)
                    if att_id:

                        attribute_id = att_search[0]

                    else:
                        attribute_id = product_attribute_obj.create({'name': att_name.lower(),'create_variant': 'always'}).id

                if 'values' in options:
                    value_list = []
                    value_id = []
                    for values in options['values']:
                        value = product_attribute_option_obj.search([('attribute_id','=',attribute_id),('name','=',values)])
                        value_search.append(value.id)
                        if value:
                            value_id = value
                        else:
                            value_id = product_attribute_option_obj.create({'name': values,'attribute_id': attribute_id})
                        value_list.append(value_id.id)

                variant.append((0,0,{'attribute_id': attribute_id,'value_ids': [(6, 0,value_list)]}))
        vals = {
            'name': products['title'] if 'title' in products else '',
            'type': "product",
            'gt_shopify_product':True,
            'gt_published_scope' : scopes,
            'gt_shopify_description': products['body_html'] if 'body_html' in products else '',
            'gt_vendor' : vendors,
            'gt_product_id' : str(products['id']) if 'id' in products else '',
            'gt_product_tags': [(6, 0, tags_lst)],
            'gt_shopify_instance_id':instance.id,
            'attribute_line_ids': variant,
            'gt_shopify_exported': True,
            'gt_shopify_product_type' : type_id,
            'company_id':company_id,
        }
        product_id = self.search([('gt_product_id','=',str(products['id'])),('gt_shopify_instance_id','=',instance.id),('gt_shopify_product','=',True)])
        if not product_id:
            self.create(vals)
        else:
            vals = {
            'name': products['title'] if 'title' in products else '',
            'type': "product",
            'gt_shopify_product':True,
            'gt_published_scope' : scopes,
            'gt_shopify_description': products['body_html'] if 'body_html' in products else '',
            'gt_vendor' : vendors,
            'gt_shopify_instance_id':instance.id,
            'attribute_line_ids': variant,
            'gt_shopify_exported': True,
            'gt_shopify_product_type' : type_id,
            'company_id':company_id,
        }
        self._cr.commit()

        if 'variants' in products and len(products['variants']) > 1:
            value_id1 = []
            value_id2 = []
            value_id3 = []
            for variant in products['variants']:
                
                value_id_list = []
                if 'option1' in variant and variant['option1'] != None and variant['option1'] != 'Default Title':
                    value_id1 = product_attribute_option_obj.search([('name','=', str(variant['option1']))])
                    if value_id1:
                        value_id_list.append(value_id1[0].id)
                   
                if 'option2' in variant and variant['option2'] != None:
                    value_id2 = product_attribute_option_obj.search([('name','=', str(variant['option2']))])
                    if value_id2:
                        value_id_list.append(value_id2[0].id)
                    
                if 'option3' in variant and variant['option3'] != None:
                    
                    value_id3 = product_attribute_option_obj.search([('name','=', str(variant['option3']))])        
                    
                    value_id_list.append(value_id3[0].id)
                product_product = product_obj.search([('default_code','=',str(products['id']))])
                if product_product:
                    for product_ids in product_product:
                        attribute_list = []
                        for att_idss in product_ids.attribute_value_ids:
                            attribute_list.append(att_idss.id)
                        if sorted(attribute_list, key=int) == sorted(value_id_list, key=int):
                            product_ids.update_variant(variant,instance,log_id)
                self._cr.commit()
            unused_product_id = product_obj.search([('default_code','=',str(products['id']))])
            if unused_product_id:
                for product_id in unused_product_id:
                    product_id.unlink()
                self._cr.commit()   
        else:
            for variant in products['variants']:
                product_product = product_obj.search([('default_code','=',str(variant['product_id']))])
                if product_product:
                    product_product.update_variant(variant,instance,log_id)
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_line_obj.create({'name':'Create Product Template','description':exc,'create_date':date.today(),
#                                      'shopify_log_id':log_id.id})
#            log_id.write({'description': 'Something went wrong'}) 
        return True
    
    
    
    
    def create_variant_ids(self):
        Product = self.env["product.product"]
        AttributeValues = self.env['product.attribute.value']
        for tmpl_id in self.with_context(active_test=False):
            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            variant_alone = tmpl_id.attribute_line_ids.filtered(lambda line: len(line.value_ids) == 1).mapped('value_ids')
            for value_id in variant_alone:
                updated_products = tmpl_id.product_variant_ids.filtered(lambda product: value_id.attribute_id not in product.mapped('attribute_value_ids.attribute_id'))
                updated_products.write({'attribute_value_ids': [(4, value_id.id)],'default_code': tmpl_id.gt_product_id,'gt_shopify_product':tmpl_id.gt_shopify_product,'gt_shopify_instance_id':tmpl_id.gt_shopify_instance_id.id})

            # iterator of n-uple of product.attribute.value *ids*
            variant_matrix = [
                AttributeValues.browse(value_ids)
                for value_ids in itertools.product(*(line.value_ids.ids for line in tmpl_id.attribute_line_ids if line.value_ids[:1].attribute_id.create_variant))
            ]

            # get the value (id) sets of existing variants
            existing_variants = {frozenset(variant.attribute_value_ids.ids) for variant in tmpl_id.product_variant_ids}
            # -> for each value set, create a recordset of values to create a
            #    variant for if the value set isn't already a variant
            to_create_variants = [
                value_ids
                for value_ids in variant_matrix
                if set(value_ids.ids) not in existing_variants
            ]

            # check product
            variants_to_activate = self.env['product.product']
            variants_to_unlink = self.env['product.product']
            for product_id in tmpl_id.product_variant_ids:
                if not product_id.active and product_id.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant) in variant_matrix:
                    variants_to_activate |= product_id
                elif product_id.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant) not in variant_matrix:
                    variants_to_unlink |= product_id
            if variants_to_activate:
                variants_to_activate.write({'active': True})

            # create new product
            for variant_ids in to_create_variants:
                new_variant = Product.create({
                    'product_tmpl_id': tmpl_id.id,
                    'attribute_value_ids': [(6, 0, variant_ids.ids)],
                    'default_code': tmpl_id.gt_product_id,
                    'gt_shopify_product':tmpl_id.gt_shopify_product,
                    'gt_shopify_instance_id':tmpl_id.gt_shopify_instance_id.id,
                })

            # unlink or inactive product
            for variant in variants_to_unlink:
                try:
                    with self._cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                        variant.unlink()
                # We catch all kind of exception to be sure that the operation doesn't fail.
                except (psycopg2.Error, except_orm):
                    variant.write({'active': False})
                    pass
        return True
    
    
    
    
    def gt_export_shopify_product(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
#        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        #product_ids = product_tmpl_obj.search([('gt_shopify_exported','=', False),('gt_shopify_product','=',True)])
       # ids = product_tmpl_obj.search([('id','=', 7)])
        #ids.write({'gt_shopify_exported':True})
        #print "product_ids++++++++++++++++",product_ids
        #self._cr.commit()
        for products in self:
            tag = ''
            if len(products.gt_product_tags) == 1:
                tag = str(products.gt_product_tags.name)
            else:
                for tags in products.gt_product_tags:
                    tag += str(tags.name)+',' 
            if len(products.product_variant_ids) == 1:
                vals = {        
                    "product": {
                        "title":str(products.name),
                        "body_html":str(products.gt_shopify_description),
                        "vendor": str(products.gt_vendor.name),
                        "product_type": str(products.gt_shopify_product_type.name),
                        "published_scope" : str(products.gt_published_scope.name or ''),
                        "tags": tag,
                        "variants": [
                            {
                              "price": str(products.lst_price),
                              #"compare_at_price": str(products.product_variant_ids.gt_compare_price),
                              "sku": str(products.default_code),
                              "inventory_policy": 'deny',
                              "fulfillment_service": 'manual',
                              "inventory_management": 'shopify',
                              "taxable": str(True),
                              "barcode": str(products.product_variant_ids.barcode) or '',
                              "weight": str(products.weight),
                              #"weight_unit": str(products.product_variant_ids.uom_id.name),
                              "requires_shipping": str(products.product_variant_ids.gt_requires_shipping),
                            }
                          ],
                    }
                }
                print ("vals++++++++",vals)
            else:
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
                            #"compare_at_price": str(variants.gt_compare_price),
                            "sku": str(variants.default_code),
                            "inventory_policy": 'deny',
                            "fulfillment_service": 'manual',
                            "inventory_management": 'shopify',
                            "taxable": str(True),
                            "barcode": str(variants.barcode) or '',
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
            payload=str(vals)
            payload=payload.replace("'",'"')
            payload=str(payload)
            shop_url = shopify_url + 'admin/products.json'
            response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
            product_rs=json.loads(response.text)  
            print ("product_rs+++++++++++++++++",product_rs)
            product = product_rs['product']
            if str(response) == '<Response [201]>':
                products.write({'gt_shopify_exported': True,'gt_product_id':product['id']})
                for variant_id in product['variants']:
                    if 'sku' in variant_id:
                        product_id = product_obj.search([('default_code','=',variant_id['sku'])])
                        if product_id:
                            product_id.write({'gt_product_id':variant_id['id'],'gt_shopify_exported': True,'gt_inventory_item_id':variant_id['inventory_item_id']})
                self._cr.commit()
                products.gt_export_shopify_image_single()
                products.gt_export_shopify_stock_single()

        #except Exception, exc:
##            pass
#            logger.error('Exception===================:  %s', exc)
        #    log_id.write({'description': exc}) 
        return True
    
    
    def gt_export_shopify_image_single(self):
#        log_obj = self.env['shopify.log']
#        log_line_obj = self.env['shopify.log.details']
#        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        photo_obj = self.env['gt.product.photo']
        #try:
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        product_ids = photo_obj.search([('gt_is_exported','=',False),('gt_shopify_instance_id','=',self.gt_shopify_instance_id.id),('gt_product_temp_id','=',self.id)])
        for products in product_ids:
            print ("template before condition",products.gt_product_temp_id.gt_product_id)
            print ("Product before condition",products.gt_product_id)
            print ("products.gt_image+++++++type",type(products.gt_image))
            print ("str(products.gt_image_name)+",str(products.gt_image_name))
            #print (errr)
            if products.gt_product_temp_id:
                #newdecode = base64.b64encode(products.gt_image)
                #decodes = base64.b64encode(newdecode)
                #decodes = base64.b64decode(products.gt_image).decode('utf-8')
                decodes = base64.b64decode(products.gt_image)
                newdecode = base64.b64encode(decodes)
#                vals = {
#                    "image": {
##                      #"position": products.gt_image_position,
##                      "attachment": newdecode, 
##                      "filename": str(products.gt_image_name),
#                        "src": "https://www.gstatic.com/webp/gallery/1.sm.jpg",
#                    }
#                  }
                vals = {
                    "image": {
                      "src": "https://upload.wikimedia.org/wikipedia/commons/2/2c/Rotating_earth_%28large%29.gif"
                    }
                  }
                #print ("vals++++++++++++++++++",vals)
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                print (payload)
                #print (error)
                shop_url = shopify_url + 'admin/api/2019-07/'+str(products.gt_product_temp_id.gt_product_id)+'/images.json'
                print ("shop_url++++++++++",shop_url)
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload, headers={'Content-Type': 'application/json',})
                print ("products+++++++++++++++",response)
                product_rs=json.loads(response.text)
                print ("product_rs+++++++++++++",product_rs)
                if str(response) == '<Response [200]>':
                    image =  product_rs['image']
                    print ("image+++++++++",image)
                    print ("writing image photo",products.write({'gt_is_exported': True,'gt_image_id':image['id'],'gt_image_src':image['src'],'gt_image_position':image['position']}))
        
            if len(self.product_variant_ids) == 1:
                for variants in self.product_variant_ids:
                    product_ids = photo_obj.search([('gt_is_exported','=',False),('gt_shopify_instance_id','=',variants.gt_shopify_instance_id.id),('gt_product_id','=',variants.id)])
                    for products in product_ids:
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
        return True
    
    
    def gt_export_shopify_stock_single(self):
#        log_obj = self.env['shopify.log']
#        log_line_obj = self.env['shopify.log.details']
#        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        quant_obj = self.env['stock.quant']
        location_id = self.env['stock.location']
        #try:
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        for products in self:
            if len(products.product_variant_ids) == 1:
                vals = {
                    "location_id": str(self.gt_shopify_instance_id.export_stock_location.gt_shopify_location_id),
                    "inventory_item_id": str(products.product_variant_ids.gt_inventory_item_id),
                    "available_adjustment": int(products.product_variant_ids.qty_available),
                  }
                payload=str(vals)
                payload=payload.replace("'",'"')
                payload=str(payload)
                print (payload)   
                shop_url = shopify_url + 'admin/inventory_levels/adjust.json'
                print ("shop_url+++++++++++++",shop_url)
                response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                product_rs=json.loads(response.text)    
                print ("product_rs+++++++++++++",product_rs)
                print (response)
            else:
                for variants in products.product_variant_ids:
                    vals = {
                        "location_id": str(self.gt_shopify_instance_id.export_stock_location.gt_shopify_location_id),
                        "inventory_item_id": str(variants.gt_inventory_item_id),
                        "available_adjustment": int(variants.qty_available),
                      }
                    payload=str(vals)
                    payload=payload.replace("'",'"')
                    payload=str(payload)
                    print (payload   )
                    shop_url = shopify_url + 'admin/inventory_levels/adjust.json'
                    print ("shop_url+++++++++++++",shop_url)
                    response = requests.post( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
                    product_rs=json.loads(response.text)    
                    print ("product_rs+++++++++++++",product_rs)
                    print (response)
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    def gt_update_shopify_product(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
#        log_id = log_obj.create({'create_date':date.today(),'name': 'Import Product','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        #try:
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        #product_ids = product_tmpl_obj.search([('gt_shopify_exported','=', False),('gt_shopify_product','=',True)])
       # ids = product_tmpl_obj.search([('id','=', 7)])
        #ids.write({'gt_shopify_exported':True})
        #print "product_ids++++++++++++++++",product_ids
        #self._cr.commit()
        for products in self:
            if products.gt_shopify_exported == True and products.gt_product_id:
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
                                  "price": str(products.lst_price),
                                  #"compare_at_price": str(products.product_variant_ids.gt_compare_price),
                                  "sku": str(products.default_code),
                                  "inventory_policy": 'deny',
                                  "fulfillment_service": 'manual',
                                  "inventory_management": 'shopify',
                                  "taxable": str(True),
                                  "barcode": str(products.product_variant_ids.barcode) or '',
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
                                #"compare_at_price": str(variants.gt_compare_price),
                                "sku": str(variants.default_code),
                                "inventory_policy": 'deny',
                                "fulfillment_service": 'manual',
                                "inventory_management": 'shopify',
                                "taxable": str(True),
                                "barcode": str(variants.barcode) or '',
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
                print( payload )  
                shop_url = shopify_url + 'admin/products/'+str(products.gt_product_id)+'.json'
#                response = requests.put( shop_url,auth=(api_key,api_pass),data=payload,  headers={'Content-Type': 'application/json',})
#                product_rs=json.loads(response.text)
#                print ("product_rs+++++++++++++",product_rs)
#                print (response)
#                product = product_rs['product']
#                if str(response) == '<Response [200]>':
#                    for variant_id in product['variants']:
#                        print ("variant_id['id']++++++++",variant_id['id'])
#                        product_id = product_obj.search([('default_code','=',variant_id['sku'])])
#                        print ("product_id+++++++++",product_id)
#                        if product_id:
#                            product_id.write({'gt_inventory_item_id':variant_id['inventory_item_id'],'gt_product_id':variant_id['id']})
#                        print ("product_id6+++++++",product_id.qty_available)
                    #self.gt_export_shopify_stock_single()
                self.gt_export_shopify_image_single()
                #print "response code",response.code
                #logger.error('Exception===================:response', response)
                
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True
    
    
    
    def gt_export_shopify_image(self):
        log_obj = self.env['shopify.log']
        log_line_obj = self.env['shopify.log.details']
        #log_id = log_obj.create({'create_date':date.today(),'name': 'Import Image','description': 'Successfull','gt_shopify_instance_id': self.id})
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        photo_obj = self.env['gt.product.photo']
        #try:
        shopify_url = str(self.gt_shopify_instance_id.gt_location)
        api_key = str(self.gt_shopify_instance_id.gt_api_key)
        api_pass = str(self.gt_shopify_instance_id.gt_password)
        product_ids = photo_obj.search([('gt_is_exported','=',False),('gt_shopify_instance_id','=',self.gt_shopify_instance_id.id),('gt_product_temp_id','=',self.id)])
        print ("product_ids++++++++0",product_ids)
        for products in product_ids:
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
                    self._cr.commit()
        if len(self.product_variant_ids) > 1:
            for product_id in self.product_variant_ids:
                print ("product_id++++++++++++++",product_id)
                product_ids = photo_obj.search([('gt_is_exported','=',False),('gt_shopify_instance_id','=',self.gt_shopify_instance_id.id),('gt_product_id','=',product_id.id)])
                for products in product_ids:
                    decodes = products.gt_image.decode("base64")
                    newdecode = decodes.encode("base64")
                    print ("Shopify Product Photo template ID",products.gt_product_id)
                    print ("template name",products.gt_product_id.name)
                    vals = {
                        "image": {
                        "variant_ids": [str(products.gt_product_id.gt_product_id)],
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
                    shop_url = shopify_url + 'admin/products/'+str(products.gt_product_id.product_tmpl_id.gt_product_id)+'/images.json'
                    print ("shop_url++++++++++",shop_url)
                    response = requests.post( shop_url,auth=(api_key,api_pass),data=payload, headers={'Content-Type': 'application/json',})
                    print ("products+++++++++++++++",response)
                    product_rs=json.loads(response.text)
                    print ("product_rs+++++++++++++",product_rs)
                    if str(response) == '<Response [200]>':
                        image =  product_rs['image']
                        print ("image+++++++++",image)
                        print ("writing image photo",products.write({'gt_is_exported': True,'gt_image_id':image['id'],'gt_image_src':image['src'],'gt_image_position':image['position']}))
                        self._cr.commit()
#                    except Exception, exc:
#                        logger.error('Exception===================:  %s', exc)
#                        log_line_obj.create({'name':'Create Image','description':exc,'create_date':date.today(),
#                                                  'shopify_log_id':log_id.id})
#                        log_id.write({'description': 'Something went wrong'}) 
#        except Exception, exc:
#            logger.error('Exception===================:  %s', exc)
#            log_id.write({'description': exc}) 
        return True 
    
    


class GtPublishedScope(models.Model):
    _name='gt.published.scope'
    _description = "The Published Scope"
    
    
    name = fields.Char(string='Scope name')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
class GtShopifyVendor(models.Model):
    _name = 'gt.shopify.vendor'
    _description = "The Shopify Vendor"
    
        
    name = fields.Char(string='Vendor name')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
    
class GtShopifyProductTags(models.Model):
    _name = 'gt.shopify.product.tags'
    _description = "The Shopify Tags"
    
    name = fields.Char(string='Product Tags')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    
    

class GtShopifyProductType(models.Model):
    _name = 'gt.shopify.product.type'
    _description = "The Shopify Product Type"
    
    name = fields.Char(string='Product Type')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
