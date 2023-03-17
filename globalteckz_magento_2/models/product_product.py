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

from odoo import fields,models,api
import requests
import json
import base64
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit='product.product'
    
    
    gl_sel_att_ids = fields.One2many('product.attribute.selection.gl', 'gl_sel_att_idc', string = 'Selection Product Attributes Global')
    wb_sel_att_ids = fields.One2many('product.attribute.selection.wb', 'wb_sel_att_idc', string = 'Selection Product Attributes Website')
    sw_sel_att_ids = fields.One2many('product.attribute.selection.sw', 'sw_sel_att_idc', string = 'Selection Product Attributes Store')
    
    gl_mul_att_ids = fields.One2many('product.attribute.multiselect.gl', 'gl_mul_att_idc', string = 'Multi-Select Product Attributes Global')
    wb_mul_att_ids = fields.One2many('product.attribute.multiselect.wb', 'wb_mul_att_idc', string = 'Multi-Select Product Attributes Website')
    sw_mul_att_ids = fields.One2many('product.attribute.multiselect.sw', 'sw_mul_att_idc', string = 'Multi-Select Product Attributes Store')
    
    gl_txt_att_ids = fields.One2many('product.attribute.txt.gl', 'gl_txt_att_idc', string = 'Text Product Attributes Global')
    wb_txt_att_ids = fields.One2many('product.attribute.txt.wb', 'wb_txt_att_idc', string = 'Text Product Attributes Website')
    sw_txt_att_ids = fields.One2many('product.attribute.txt.sw', 'sw_txt_att_idc', string = 'Text Product Attributes Store')
    
    gl_flt_att_ids = fields.One2many('product.attribute.flt.gl', 'gl_flt_att_idc', string = 'Float Product Attributes Global')
    wb_flt_att_ids = fields.One2many('product.attribute.flt.wb', 'wb_flt_att_idc', string = 'Float Product Attributes Website')
    sw_flt_att_ids = fields.One2many('product.attribute.flt.sw', 'sw_flt_att_idc', string = 'Float Product Attributes Store')
    
    gl_dte_att_ids = fields.One2many('product.attribute.dte.gl', 'gl_dte_att_idc', string = 'Date Product Attributes Global')
    wb_dte_att_ids = fields.One2many('product.attribute.dte.wb', 'wb_dte_att_idc', string = 'Date Product Attributes Website')
    sw_dte_att_ids = fields.One2many('product.attribute.dte.sw', 'sw_dte_att_idc', string = 'Date Product Attributes Store')

    magento_instance_ids = fields.Many2many('gt.magento.instance','mage_prod_rel','insta_id','pprroo_id','Magento Instance')
    magento_id = fields.Char(string='Magento ID')
    magento_product = fields.Boolean(string='Magento Product')
    #tier_price_ids = fields.One2many('products.tier.price','product_id','Tier Price')
    product_type = fields.Selection([('simple', 'Simple Product'),
    ('configurable', 'Configurable Product'),('grouped', 'Grouped Product'),('virtual', 'Virtual Product'),
    ('bundle', 'Bundle Product'),('mygrouped', 'My Grouped'),('downloadable', 'Downloadable Product')],
    'Type', default='simple')
    #prod_images= fields.One2many('product.photo', 'product_id',string='Images')
    attribute_set = fields.Many2one('gt.product.attribute.set', string='Attribute Set')
    prod_category_id =fields.Many2many('product.category','us_template_rel','temp_id','categ_id','Category')
    product_image_id = fields.One2many('product.photo', 'product_id',string='Images')
    store_ids = fields.Many2many('gt.magento.store','prod_str_rel','prod_id','stor_id','Store')
    exported_magento = fields.Boolean(string='Magento Exported')
    website_ids = fields.Many2many('gt.magento.website','prod_web_rel','prweb_id','webs_id','Website')
    gt_magento_product_ids = fields.Many2many('gt.magento.product.multi', 'tags_product_rel', 'produ_id', 'mag_id', string='Product ID')
    
    
    def create_configurable_magento_products(self, instance, headers, sku, store_id, website_id):
        prod_att_obj = self.env['product.attribute']
        attribute_obj =self.env['gt.product.attributes']
        prod_att_option_obj = self.env['gt.product.attribute.options']
        prod_temp_att_val_obj = self.env['product.template.attribute.value']
        prod_tmp_obj = self.env['product.template']

        url = str(instance.location)+"/rest/"+str(store_id.code)+"/V1/products/"+str(sku).encode('utf-8').decode()
        response = requests.request("GET",url, headers=headers)
        each_product = json.loads(response.text)
        attributes = []
        variant_list = []
        attributes_name = []
        instance_ids = []
        line_categ = []
        categ_id = False
        product_id = prod_tmp_obj.search([('magento_sku', '=', str(sku))])
        if not product_id:
            print("*==> New product:: ", product_id.name)
            if each_product.get('extension_attributes',False):
                if each_product['extension_attributes'].get('configurable_product_options',False):               
                    for option in each_product['extension_attributes'].get('configurable_product_options'):
                        attribute_mag_ids = attribute_obj.search([
                            ('magento_id','=',option.get('attribute_id')),
                            ('referential_id','=',instance.id)
                        ])
                        if attribute_mag_ids:# atribute magento
                            attribute_ids = prod_att_obj.search([
                                ('attribute_magento_id','=',option.get('attribute_id')),
                                ('is_attribute_magento','=',True)
                            ])
                            if attribute_ids: # atribute odoo
                                attribute = attribute_ids[0]                           
                            else:
                                new_vals={
                                    'name':option.get('label'),
                                    'create_variant':'always'
                                    }
                                attribute = prod_att_obj.create(new_vals)
                                print("*==> create odoo atribute! ::",new_vals)
                            if not list(filter(lambda item: item['attribute'] == attribute.id, attributes)):
                                attribute_dict = {
                                    'attribute': attribute.id,
                                    'values': [],
                                }
                                variant_list_attr = []
                                for values in option.get('values'):
                                    prod_opt_ids = prod_att_option_obj.search([
                                        ('value', '=', values['value_index'])
                                    ]).filtered(lambda x: x.attribute_id.odoo_attr_id == attribute)
                                    if prod_opt_ids:# values of atribute in magento
                                        if prod_opt_ids[0].product_attr_value.id not in variant_list_attr:
                                            variant_list_attr.append(prod_opt_ids[0].product_attr_value.id)
                                    else:
                                        print ("*==> THE PRODUCT DOES NOT HAVE OPTIONAL VALUES, IT MAY NOT HAVE BEEN IMPORTED: %s" % values['value_index']),
                                attribute_dict['values'] = variant_list_attr
                                attributes.append(attribute_dict)
            if attributes:
                for att_line in attributes:
                    variant_list.append((0,0,{
                        'attribute_id': att_line.get('attribute'),
                        'value_ids':[(6, 0, att_line.get('values'))]
                    }))
            if len(self.magento_instance_ids) > 0:
                for old_instance_id in self.magento_instance_ids:
                    instance_ids.append(old_instance_id.id)
            if instance.id not in instance_ids:
                instance_ids.append(instance.id) 

            prod_cat_obj=self.env['product.category']
            if each_product.get('custom_attributes'):
                for attributes_child in each_product.get('custom_attributes'):
                    if attributes_child['attribute_code'] == 'category_ids':
                        categ_id = attributes_child['value']
                        for each_category in categ_id:
                            cat_ids=prod_cat_obj.search([
                                ('magento_id','=',each_category),
                                ('magento_instance_id','=',instance.id),
                                ('shop_id','=',store_id.id),
                            ])
                            if cat_ids:
                                line_categ.append(cat_ids.id)
                    if attributes_child['attribute_code'] == 'ds_category':
                        categ_att_id =  self.env['gt.product.attributes'].search([
                            ('attribute_code', '=', 'ds_category'),
                            ('referential_id', '=', instance.id),
                        ])
                        categ_att_option_id = self.env['gt.product.attribute.options'].search([
                            ('value', '=', attributes_child['value']),
                            ('referential_id', '=', instance.id),
                            ('attribute_id', '=', categ_att_id.id)
                        ])

            product_tmp_vals = {  
                'default_code':str(sku),
                'name':str(each_product.get('name')),
                'lst_price':each_product.get('price'),
                'magento_id':str(each_product.get('id')),
                'attribute_line_ids':variant_list or False,
                'type':'product',
                'magento_template':True,
                'magento_exported':True,
                'magento_sku': str(sku),
                'magento_instance_ids':[(6,0,instance_ids)],
                'prod_category_id':[(6,0,line_categ)],
                'prod_attr_category_id': categ_att_option_id.id if categ_att_option_id else False,
            }
            product_tmp_id = prod_tmp_obj.create(product_tmp_vals)
            print("*==> create product template! ::",product_tmp_vals)
            self._cr.commit()
            url = instance.location+"/rest/V1/configurable-products/"+str(product_tmp_id.magento_sku).encode('utf-8').decode()+"/children" 
            response = requests.request("GET",url, headers=headers)
            child_product_list=json.loads(response.text)
            
            for child_product in child_product_list:           
                value_id_list = []
                for att_name in attributes:
                    attribute_magento = attribute_obj.search([
                        ('odoo_attr_id', '=', int(att_name['attribute']))
                    ])# atribute magento
                    for child in child_product.get('custom_attributes'):
                        if child.get('attribute_code') == attribute_magento.attribute_code:
                            value_id = prod_att_option_obj.search([
                                ('value','=',child.get('value')),
                                ('attribute_id', '=', attribute_magento.attribute_code)
                            ])# value of atribute magento
                            if value_id:
                                value_id_list.append(value_id.product_attr_value.id)
                product_product = self.search([('magento_id','=',str(each_product.get('id')))])
                if product_product:
                    for product_ids in product_product:
                        attribute_list = []
                        for att_idss in product_ids.product_template_attribute_value_ids:
                            attribute_list.append(att_idss.product_attribute_value_id.id)
                        if sorted(attribute_list, key=int) == sorted(value_id_list, key=int):
                            product_ids.update_variant(child_product['sku'],instance,product_ids,headers,store_id,website_id)
                    self._cr.commit()
        else:
            print("*==> product doesnt exist:: ", product_id.name)
            if each_product['extension_attributes'].get('configurable_product_links',False):
                for option in each_product['extension_attributes'].get('configurable_product_links'):
                    product_id = self.search([('magento_id','=',str(option))])
                    if product_id:
                        product_id.update_variant(product_id.default_code,instance,product_id,headers,store_id,website_id)
        instance.write({'config_prod_from_id': str(each_product.get('id'))})
        self._cr.commit()                  
        return True
       
    def create_simple_products(self,instance,headers,sku,store_id,website_id):
        multi_instance = self.env['gt.magento.product.multi']
        categ_id = []
        line_categ = []
        store_ids = []
        website_ids = []
        instance_ids = []
        att_set_obj = self.env['gt.product.attribute.set']
        url=str(instance.location)+"/rest/"+str(store_id.code)+"/V1/products/"+str(sku).encode('utf-8').decode()
        response = requests.request("GET",url, headers=headers)
        if str(response.status_code)=="200":
            each_product=json.loads(response.text)
            att_ids = att_set_obj.search([
                ('code','=',each_product.get('attribute_set_id')),
                ('magento_instance_id','=',instance.id)
            ]) # atribute set of magento
            if len(self.store_ids) > 0:
                for old_store_id in self.store_ids:
                    store_ids.append(old_store_id)
            if len(self.website_ids) > 0:
                for old_website_id in self.website_ids:
                    website_ids.append(old_website_id)
            if len(self.magento_instance_ids) > 0:
                for old_instance_id in self.magento_instance_ids:
                    instance_ids.append(old_instance_id.id)
            if store_id.id not in store_ids:
                store_ids.append(store_id.id)
            if website_id.id not in website_ids:
                website_ids.append(website_id.id)
            if instance.id not in instance_ids:
                instance_ids.append(instance.id)
            if att_ids:
                att_id=att_ids.id
            else:
                att_id=False
            if each_product.get('custom_attributes'):
                for attributes_child in each_product.get('custom_attributes'):
                    if attributes_child['attribute_code']=='category_ids':
                        categ_id = attributes_child['value']
                        for each_category in categ_id:
                            prod_cat_obj=self.env['product.category']
                            cat_ids=prod_cat_obj.search([
                                ('magento_id','=',each_category),
                                ('magento_instance_id','=',instance.id),
                                ('shop_id','=',store_id.id)
                            ])
                            if cat_ids:
                                line_categ.append(cat_ids.id)
            vals = {
                'name':each_product.get('name'),
                'default_code':sku,
                'magento_id':each_product['id'],
                'attribute_set':att_id,
                'magento_product':True,
                'product_type':each_product.get('type_id'),
                'type':'product',
                'lst_price':each_product.get('price'),
                'prod_category_id':[(6,0,line_categ)],
                'website_ids':[(6,0,website_ids)],
                'store_ids':[(6,0,store_ids)],
                'exported_magento': True,
                'magento_instance_ids':[(6,0,instance_ids)]
            }
            product_id=self.search([('magento_id','=',each_product['id'])])
            if product_id:
                print ("THE PRODUCT ALREADY EXISTS!, upgrating.. :: ",vals)
                product_id.write(vals)
                self.create_update_attributes(each_product,instance,product_id,store_id,website_id)
            else:
                product_id = self.create(vals)            
                self.create_update_attributes(each_product,instance,product_id,store_id,website_id)
            self._cr.commit()
            instance_id = multi_instance.search([
                ('magento_id','=',each_product['id']),
                ('gt_magento_instance_id','=',instance.id),
                ('gt_magento_exported','=',True),
                ('product_id','=',product_id.id)
            ])
            if not instance_id:
                instance_id = multi_instance.create({
                    'magento_id':each_product['id'],
                    'gt_magento_instance_id':instance.id,
                    'gt_magento_exported':True,
                    'product_id':product_id.id
                })
            prods_id = []
            for prod_id in product_id.gt_magento_product_ids:
                prods_id.append(prod_id.id)
            if instance_id.id not in prods_id:
                prods_id.append(instance_id.id)
            product_id.write({'gt_magento_product_ids':[(6,0,prods_id)]})
            instance.write({'from_id': each_product['id']})
            return product_id
        else:
            product_id = []
            
    def create_simple_products_orders(self,instance,headers,sku,store_id,website_id,magento_product_id):
        product_id = []
        url=str(instance.location)+"/rest/"+str(store_id.code)+"/V1/products/"+str(sku).encode('utf-8').decode()
        response = requests.request("GET",url, headers=headers)
        if str(response.status_code)!="200":
            url=str(instance.location)+"/rest/V1/products? searchCriteria[filterGroups][0][filters][0][field]=entity_id& searchCriteria[filterGroups][0][filters][0][value]="+str(magento_product_id)+"& searchCriteria[filterGroups][0][filters][0][conditionType]=eq"
            response = requests.request("GET",url, headers=headers)
            if str(response.status_code)=="200":
                each_product=json.loads(response.text)
                if each_product['items']:
                    product_id = self.create_main_order_products(instance,sku,store_id,website_id,each_product['items'][0])
                
        else:
            each_product=json.loads(response.text)
            product_id = self.create_main_order_products(instance,sku,store_id,website_id,each_product)
        return product_id
                
    def create_main_order_products(self,instance,sku,store_id,website_id,each_product):
        instance_ids = []
        categ_id = []
        line_categ = []
        store_ids = []
        website_ids = []
        multi_instance = self.env['gt.magento.product.multi']
        att_set_obj = self.env['gt.product.attribute.set']
        att_ids=att_set_obj.search([
            ('code','=',each_product.get('attribute_set_id')),
            ('magento_instance_id','=',instance.id)
        ])
        if len(self.store_ids) > 0:
            for old_store_id in self.store_ids:
                store_ids.append(old_store_id)
        if len(self.website_ids) > 0:
            for old_website_id in self.website_ids:
                website_ids.append(old_website_id)
        if len(self.magento_instance_ids) > 0:
            for old_instance_id in self.magento_instance_ids:
                instance_ids.append(old_instance_id.id)
        if store_id.id not in store_ids:
            store_ids.append(store_id.id)
        if website_id.id not in website_ids:
            website_ids.append(website_id.id)
        if instance.id not in instance_ids:
            instance_ids.append(instance.id)
        if att_ids:
            att_id=att_ids.id
        else:
            att_id=False
        if each_product.get('custom_attributes'):
            for attributes_child in each_product.get('custom_attributes'):
                if attributes_child['attribute_code']=='category_ids':
                    categ_id = attributes_child['value']  
                    for each_category in categ_id:
                        prod_cat_obj=self.env['product.category']
                        cat_ids=prod_cat_obj.search([
                            ('magento_id','=',each_category),
                            ('magento_instance_id','=',instance.id),
                            ('shop_id','=',store_id.id)
                        ])
                        if cat_ids:
                            line_categ.append(cat_ids.id)
        vals = {
            'name':each_product.get('name'),
            'default_code':sku,
            'magento_id':each_product['id'],
            'attribute_set':att_id,
            'magento_product':True,
            'product_type':each_product.get('type_id'),
            'type':'product',
            'lst_price':each_product.get('price'),
            'prod_category_id':[(6,0,line_categ)],
            'website_ids':[(6,0,website_ids)],
            'store_ids':[(6,0,store_ids)],
            'exported_magento': True,
            'magento_instance_ids':[(6,0,instance_ids)]
        }
        product_id=self.search([('magento_id','=',each_product['id'])])
        if product_id:
            print ("*==> WRITING THE FINAL VARIANT PRODUCT! :: ",vals)
            product_id.write(vals)
            self.create_update_attributes(each_product,instance,product_id,store_id,website_id)
        else:
            product_id = self.create(vals)            
            self.create_update_attributes(each_product,instance,product_id,store_id,website_id)
        self._cr.commit()
        instance_id = multi_instance.search([
            ('magento_id','=',each_product['id']),
            ('gt_magento_instance_id','=',instance.id),
            ('gt_magento_exported','=',True),
            ('product_id','=',product_id.id)
        ])
        if not instance_id:
            instance_id = multi_instance.create({
                'magento_id':each_product['id'],
                'gt_magento_instance_id':instance.id,
                'gt_magento_exported':True,
                'product_id':product_id.id
            })
        prods_id = []
        for prod_id in product_id.gt_magento_product_ids:
            prods_id.append(prod_id.id)
        if instance_id.id not in prods_id:
            prods_id.append(instance_id.id)
        product_id.write({'gt_magento_product_ids':[(6,0,prods_id)]})
        
        return product_id

    def update_variant(self,sku,instance,product_ids,headers,store_id,website_id):
        att_set_obj = self.env['gt.product.attribute.set']
        multi_instance = self.env['gt.magento.product.multi']
        categ_id = []
        line_categ = []
        store_ids = []
        website_ids = []
        instance_ids = []
        print ("*==> sku:: ",str(sku))
        url=instance.location+"/rest/"+str(store_id.code)+"/V1/products/"+str(sku)
        response = requests.request("GET",url, headers=headers)
        if str(response.status_code)=="200":
            each_list=json.loads(response.text)
            self.create_update_attributes(each_list,instance,product_ids,store_id,website_id)
            if len(self.store_ids) > 0:
                for old_store_id in self.store_ids:
                    store_ids.append(old_store_id.id)
            if len(self.website_ids) > 0:
                for old_website_id in self.website_ids:
                    website_ids.append(old_website_id.id)
            if len(self.magento_instance_ids) > 0:
                for old_instance_id in self.magento_instance_ids:
                    instance_ids.append(old_instance_id.id)
            if store_id.id not in store_ids:
                store_ids.append(store_id.id)
            if website_id.id not in website_ids:
                website_ids.append(website_id.id)
            if instance.id not in instance_ids:
                instance_ids.append(instance.id)
            att_ids=att_set_obj.search([
                ('code','=',each_list.get('attribute_set_id')),
                ('magento_instance_id','=',instance.id)
            ])
            if att_ids:
                att_id=att_ids.id
            else:
                att_id=False
            if each_list.get('custom_attributes'):
                for attributes_child in each_list.get('custom_attributes'):
                    if attributes_child['attribute_code']=='category_ids':
                        categ_id = attributes_child['value']  
                        for each_category in categ_id:
                            prod_cat_obj=self.env['product.category']
                            cat_ids=prod_cat_obj.search([
                                ('magento_id','=',each_category),
                                ('magento_instance_id','=',instance.id),
                                ('shop_id','=',store_id.id)
                            ])
                            if cat_ids:
                                line_categ.append(cat_ids.id)
            instance_id = multi_instance.search([
                ('magento_id','=',each_list['id']),
                ('gt_magento_instance_id','=',instance.id),
                ('gt_magento_exported','=',True),
                ('product_id','=',product_ids.id)
            ])
            if not instance_id:
                instance_id = multi_instance.create({
                    'magento_id':each_list['id'],
                    'gt_magento_instance_id':instance.id,
                    'gt_magento_exported':True,
                    'product_id':product_ids.id
                })
            prods_id = []
            for prod_id in product_ids.gt_magento_product_ids:
                prods_id.append(prod_id.id)
            if instance_id.id not in prods_id:
                prods_id.append(instance_id.id)
            vals = {'default_code':sku,'magento_id':each_list['id'],
                    'attribute_set':att_id,
                    'magento_instance_ids':[(6,0,instance_ids)],
                    'magento_product':True,
                    'product_type':each_list.get('type_id'),
                    'type':'product',
                    'lst_price':each_list.get('price'),
                    'prod_category_id':[(6,0,line_categ)],
                    'website_ids':[(6,0,website_ids)],
                    'store_ids':[(6,0,store_ids)],
                    'exported_magento': True,
                    'gt_magento_product_ids':[(6,0,prods_id)]}
            print ("*==> WRITING THE FINAL VARIANT PRODUCT::",product_ids.write(vals))
        return True
     
    def create_update_attributes(self,each_list,instance,product_ids,store_id,website_id):
        attribute_obj =self.env['gt.product.attributes']
        prod_att_option_obj=self.env['gt.product.attribute.options']
        status_id = attribute_obj.search([('attribute_code','=','status'),('referential_id','=',instance.id)])
        if status_id and status_id.scope == 'global':
            option_id = prod_att_option_obj.search([('value','=',each_list.get('status')),('attribute_id','=',status_id.id),('referential_id','=',instance.id)])
            if option_id:
                status_ids = self.env['product.attribute.selection.gl'].search([('gl_sel_att_id','=',status_id.id),
                ('gl_sel_att_opt_id','=', option_id.id),('gl_sel_att_idc','=',product_ids.id),('gl_sel_mag_inst_id','=',instance.id)])
                if not status_ids:
                    self.env['product.attribute.selection.gl'].create({'gl_sel_att_id':status_id.id,
                    'gl_sel_att_opt_id':option_id.id,'gl_sel_att_idc':product_ids.id,'gl_sel_mag_inst_id':instance.id})
        elif status_id and status_id.scope == 'website':
            option_id = prod_att_option_obj.search([('value','=',each_list.get('status')),('attribute_id','=',status_id.id)])
            if option_id:
                status_ids = self.env['product.attribute.selection.wb'].search([('wb_sel_att_id','=',status_id.id),('wb_sel_mag_inst_id','=',instance.id),
                ('wb_sel_att_opt_id','=',option_id.id),('wb_sel_att_idc','=',product_ids.id),('wb_sel_mag_web_id','=',website_id.id)])
                if not status_ids:
                    self.env['product.attribute.selection.wb'].create({'wb_sel_att_id':status_id.id,'wb_sel_mag_inst_id':instance.id,
                    'wb_sel_att_opt_id':option_id.id,'wb_sel_att_idc':product_ids.id,'wb_sel_mag_web_id':website_id.id})
        elif status_id and status_id.scope == 'store':
            option_id = prod_att_option_obj.search([('value','=',each_list.get('status')),('attribute_id','=',status_id.id)])
            if option_id:
                status_ids = self.env['product.attribute.selection.sw'].search([('sw_sel_att_id','=',status_id.id),('sw_sel_mag_inst_id','=',instance.id),
                ('sw_sel_att_opt_id','=',option_id.id),('sw_sel_att_idc','=',product_ids.id),('sw_sel_mag_str_id','=',store_id.id)])
                if not status_ids:
                    self.env['product.attribute.selection.sw'].create({'sw_sel_att_id':status_id.id,'sw_sel_mag_inst_id':instance.id,
                    'sw_sel_att_opt_id':option_id.id,'sw_sel_att_idc':product_ids.id,'sw_sel_mag_str_id':store_id.id})
            
        visibility_id = attribute_obj.search([('attribute_code','=','visibility'),('referential_id','=',instance.id)])
        if visibility_id and visibility_id.scope == 'global':
            option_id = prod_att_option_obj.search([('value','=',each_list.get('status')),('attribute_id','=',visibility_id.id),('referential_id','=',instance.id)])
            if option_id:
                visibility_ids = self.env['product.attribute.selection.gl'].search([('gl_sel_att_id','=',visibility_id.id),
                ('gl_sel_att_opt_id','=', option_id.id),('gl_sel_att_idc','=',product_ids.id),('gl_sel_mag_inst_id','=',instance.id)])
                if not visibility_ids:
                    self.env['product.attribute.selection.gl'].create({'gl_sel_att_id':visibility_id.id,
                    'gl_sel_att_opt_id':option_id.id,'gl_sel_att_idc':product_ids.id,'gl_sel_mag_inst_id':instance.id})
        elif visibility_id and visibility_id.scope == 'website':
            option_id = prod_att_option_obj.search([('value','=',each_list.get('status')),('attribute_id','=',visibility_id.id)])
            if option_id:
                visibility_ids = self.env['product.attribute.selection.wb'].search([('wb_sel_att_id','=',visibility_id.id),('wb_sel_mag_web_id','=',instance.id),
                ('wb_sel_att_opt_id','=',option_id.id),('wb_sel_att_idc','=',product_ids.id),('wb_sel_mag_web_id','=',website_id.id)])
                if not visibility_ids:
                    self.env['product.attribute.selection.wb'].create({'wb_sel_att_id':visibility_id.id,'wb_sel_mag_web_id':instance.id,
                    'wb_sel_att_opt_id':option_id.id,'wb_sel_att_idc':product_ids.id,'wb_sel_mag_web_id':website_id.id})
        elif visibility_id and visibility_id.scope == 'store':
            option_id = prod_att_option_obj.search([('value','=',each_list.get('status')),('attribute_id','=',visibility_id.id)])
            if option_id:
                visibility_ids = self.env['product.attribute.selection.sw'].search([('sw_sel_att_id','=',visibility_id.id),('sw_sel_mag_inst_id','=',instance.id),
                ('sw_sel_att_opt_id','=',option_id.id),('sw_sel_att_idc','=',product_ids.id),('sw_sel_mag_str_id','=',store_id.id)])
                if not visibility_ids:
                    self.env['product.attribute.selection.sw'].create({'sw_sel_att_id':visibility_id.id,'sw_sel_mag_inst_id':instance.id,
                    'sw_sel_att_opt_id':option_id.id,'sw_sel_att_idc':product_ids.id,'sw_sel_mag_str_id':store_id.id})

#ATTRIBUTES ODOO
        for attributes_odoo in each_list.get('custom_attributes'):
            attribute_id = attribute_obj.search([('attribute_code','=',attributes_odoo.get('attribute_code')),('referential_id','=',instance.id)])
            
            if attribute_id and attribute_id.frontend_input_id.name_type == 'select':
                if attribute_id.scope == 'global':
                    option_id = prod_att_option_obj.search([('value','=',attributes_odoo.get('value')),('attribute_id','=',attribute_id.id),('referential_id','=',instance.id)])
                    if option_id:
                        gl_sel_att_id = self.env['product.attribute.selection.gl'].search([('gl_sel_att_id','=',attribute_id.id),
                        ('gl_sel_att_opt_id','=', option_id.id),('gl_sel_att_idc','=',product_ids.id),('gl_sel_mag_inst_id','=',instance.id)])
                        if not gl_sel_att_id:
                            self.env['product.attribute.selection.gl'].create({'gl_sel_att_id':attribute_id.id,
                            'gl_sel_att_opt_id':option_id.id,'gl_sel_att_idc':product_ids.id,'gl_sel_mag_inst_id':instance.id})
                elif attribute_id.scope == 'website':
                    option_id = prod_att_option_obj.search([('value','=',attributes_odoo.get('value')),('attribute_id','=',attribute_id.id)])
                    if option_id:
                        wb_sel_att_id = self.env['product.attribute.selection.wb'].search([('wb_sel_att_id','=',attribute_id.id),('wb_sel_mag_inst_id','=',instance.id),
                        ('wb_sel_att_opt_id','=',option_id.id),('wb_sel_att_idc','=',product_ids.id),('wb_sel_mag_web_id','=',website_id.id)])
                        if not wb_sel_att_id:
                            self.env['product.attribute.selection.wb'].create({'wb_sel_att_id':attribute_id.id,'wb_sel_mag_inst_id':instance.id,
                            'wb_sel_att_opt_id':option_id.id,'wb_sel_att_idc':product_ids.id,'wb_sel_mag_web_id':website_id.id})
                elif attribute_id.scope == 'store':
                    option_id = prod_att_option_obj.search([('value','=',attributes_odoo.get('value')),('attribute_id','=',attribute_id.id)])
                    if option_id:
                        wb_sel_att_id = self.env['product.attribute.selection.sw'].search([('sw_sel_att_id','=',attribute_id.id),('sw_sel_mag_inst_id','=',instance.id),
                        ('sw_sel_att_opt_id','=',option_id.id),('sw_sel_att_idc','=',product_ids.id),('sw_sel_mag_str_id','=',store_id.id)])
                        if not wb_sel_att_id:
                            self.env['product.attribute.selection.sw'].create({'sw_sel_att_id':attribute_id.id,'sw_sel_mag_inst_id':instance.id,
                            'sw_sel_att_opt_id':option_id.id,'sw_sel_att_idc':product_ids.id,'sw_sel_mag_str_id':store_id.id})
            
            elif attribute_id and attribute_id.frontend_input_id.name_type == 'multiselect':
                if attribute_id.scope == 'global':
                    my_list = attributes_odoo.get('value').split(",")
                    line_option=[]
                    for value in my_list:
                        option_id = prod_att_option_obj.search([('value','=',value),('attribute_id','=',attribute_id.id),('referential_id','=',instance.id)])
                        if option_id:
                            line_option.append(option_id.id)
                    if line_option:
                        wb_mul_att_opt_id = self.env['product.attribute.multiselect.gl'].search([('gl_mul_att_id','=',attribute_id.id),
                        ('gl_mul_att_idc','=',product_ids.id),('gl_mul_mag_inst_id','=',instance.id)])
                        if not wb_mul_att_opt_id:
                            wb_mul_att_opt_id = self.env['product.attribute.multiselect.gl'].create({'gl_mul_att_id':attribute_id.id,
                            'gl_mul_att_opt_id':[(6,0,line_option)],'gl_mul_att_idc':product_ids.id,'gl_mul_mag_inst_id':instance.id})    
                
                elif attribute_id.scope == 'website':
                    my_list = attributes_odoo.get('value').split(",")
                    line_option=[]
                    for value in my_list:
                        option_id = prod_att_option_obj.search([('value','=',value),('attribute_id','=',attribute_id.id),('referential_id','=',instance.id)])
                        if option_id:
                            line_option.append(option_id.id)
                    if line_option:
                        wb_sel_att_id = self.env['product.attribute.multiselect.wb'].search([('wb_mul_att_id','=',attribute_id.id),('wb_mul_mag_web_id','=',instance.id),
                        ('wb_mul_att_idc','=',product_ids.id),('wb_mul_mag_web_id','=',website_id.id)])
                        if not wb_sel_att_id:
                            self.env['product.attribute.multiselect.wb'].create({'wb_mul_att_id':attribute_id.id,'wb_mul_mag_web_id':instance.id,
                            'wb_mul_att_opt_id':[(6,0,line_option)],'wb_mul_att_idc':product_ids.id,'wb_mul_mag_web_id':website_id.id})               
                
                elif attribute_id.scope == 'store':
                    my_list = attributes_odoo.get('value').split(",")
                    line_option=[]
                    for value in my_list:
                        option_id = prod_att_option_obj.search([('value','=',value),('attribute_id','=',attribute_id.id),('referential_id','=',instance.id)])
                        if option_id:
                            line_option.append(option_id.id)
                    if line_option:
                        wb_sel_att_id = self.env['product.attribute.multiselect.sw'].search([('sw_mul_att_id','=',attribute_id.id),('sw_mul_mag_inst_id','=',instance.id),
                        ('sw_mul_att_idc','=',product_ids.id),('sw_mul_mag_str_id','=',store_id.id)])
                        if not wb_sel_att_id:
                            self.env['product.attribute.multiselect.sw'].create({'sw_mul_att_id':attribute_id.id,'sw_mul_mag_inst_id':instance.id,
                            'sw_mul_att_opt_id':[(6,0,line_option)],'sw_mul_att_idc':product_ids.id,'sw_mul_mag_str_id':store_id.id})
            elif attribute_id and attribute_id.frontend_input_id.name_type == 'textarea' or attribute_id.frontend_input_id.name_type == 'text' and attribute_id.attribute_code != 'category_ids':
                if attribute_id.scope == 'global':
                    gl_txt_att_id = self.env['product.attribute.txt.gl'].search([('gl_txt_att_id','=',attribute_id.id),
                    ('gl_txt_att_opt','=',str(attributes_odoo.get('value'))),('gl_txt_att_idc','=',product_ids.id),('gl_txt_mag_inst_id','=',instance.id)])
                    if not gl_txt_att_id:
                        gl_txt_att_id = self.env['product.attribute.txt.gl'].create({'gl_txt_att_id':attribute_id.id,
                        'gl_txt_att_opt':str(attributes_odoo.get('value')),'gl_txt_att_idc':product_ids.id,'gl_txt_mag_inst_id':instance.id})
                elif attribute_id.scope == 'website':
                    wb_txt_att_id = self.env['product.attribute.txt.wb'].search([('wb_txt_att_id','=',attribute_id.id),('wb_txt_mag_web_id','=',instance.id),
                    ('wb_txt_att_opt','=',str(attributes_odoo.get('value'))),('wb_txt_att_idc','=',product_ids.id),('wb_txt_mag_web_id','=',website_id.id)])
                    if not wb_txt_att_id:
                        wb_txt_att_id = self.env['product.attribute.txt.wb'].create({'wb_txt_att_id':attribute_id.id,'wb_txt_mag_web_id':instance.id,
                        'wb_txt_att_opt':str(attributes_odoo.get('value')),'wb_txt_att_idc':product_ids.id,'wb_txt_mag_web_id':website_id.id})
                elif attribute_id.scope == 'store':
                    sw_txt_att_id = self.env['product.attribute.txt.sw'].search([('sw_txt_att_id','=',attribute_id.id),('sw_txt_mag_inst_id','=',instance.id),
                    ('sw_txt_att_opt','=',str(attributes_odoo.get('value'))),('sw_txt_att_idc','=',product_ids.id),('sw_txt_mag_str_id','=',store_id.id)])
                    if not sw_txt_att_id:
                        sw_txt_att_id = self.env['product.attribute.txt.sw'].create({'sw_txt_att_id':attribute_id.id,'sw_txt_mag_inst_id':instance.id,
                        'sw_txt_att_opt':str(attributes_odoo.get('value')),'sw_txt_att_idc':product_ids.id,'sw_txt_mag_str_id':store_id.id})
                        
            elif attribute_id and attribute_id.frontend_input_id.name_type == 'price' or attribute_id.frontend_input_id.name_type == 'weight':
                if attribute_id.scope == 'global':
                    gl_flt_att_id = self.env['product.attribute.flt.gl'].search([('gl_flt_att_id','=',attribute_id.id),
                    ('gl_flt_att_opt','=',str(attributes_odoo.get('value'))),('gl_flt_att_idc','=',product_ids.id),('gl_flt_mag_inst_id','=',instance.id)])
                    if not gl_flt_att_id:
                        gl_txt_att_id = self.env['product.attribute.flt.gl'].create({'gl_flt_att_id':attribute_id.id,
                        'gl_flt_att_opt':str(attributes_odoo.get('value')),'gl_flt_att_idc':product_ids.id,'gl_flt_mag_inst_id':instance.id})
                elif attribute_id.scope == 'website':
                    wb_flt_att_id = self.env['product.attribute.flt.wb'].search([('wb_flt_att_id','=',attribute_id.id),('wb_flt_mag_inst_id','=',instance.id),
                    ('wb_flt_att_opt','=',str(attributes_odoo.get('value'))),('wb_flt_att_idc','=',product_ids.id),('wb_flt_mag_web_id','=',website_id.id)])
                    if not wb_flt_att_id:
                        wb_txt_att_id = self.env['product.attribute.flt.wb'].create({'wb_flt_att_id':attribute_id.id,'wb_flt_mag_inst_id':instance.id,
                        'wb_flt_att_opt':str(attributes_odoo.get('value')),'wb_flt_att_idc':product_ids.id,'wb_flt_mag_web_id':website_id.id})
                elif attribute_id.scope == 'store':
                    sw_flt_att_id = self.env['product.attribute.flt.sw'].search([('sw_flt_att_id','=',attribute_id.id),('sw_flt_mag_inst_id','=',instance.id),
                    ('sw_flt_att_opt','=',str(attributes_odoo.get('value'))),('sw_flt_att_idc','=',product_ids.id),('sw_flt_mag_str_id','=',store_id.id)])
                    if not sw_flt_att_id:
                        sw_flt_att_id = self.env['product.attribute.flt.sw'].create({'sw_flt_att_id':attribute_id.id,'sw_flt_mag_inst_id':instance.id,
                        'sw_flt_att_opt':str(attributes_odoo.get('value')),'sw_flt_att_idc':product_ids.id,'sw_flt_mag_str_id':store_id.id})
                                              
            elif attribute_id and attribute_id.frontend_input_id.name_type == 'date':
                if attribute_id.scope == 'global':
                    gl_flt_att_id = self.env['product.attribute.dte.gl'].search([('gl_dte_att_id','=',attribute_id.id),
                    ('gl_dte_att_opt','=',str(attributes_odoo.get('value'))),('gl_dte_att_idc','=',product_ids.id),('gl_dte_mag_inst_id','=',instance.id)])
                    if not gl_txt_att_id:
                        gl_txt_att_id = self.env['product.attribute.dte.gl'].create({'gl_dte_att_id':attribute_id.id,
                        'gl_dte_att_opt':str(attributes_odoo.get('value')),'gl_dte_att_idc':product_ids.id,'gl_dte_mag_inst_id':instance.id})
                elif attribute_id.scope == 'website':
                    wb_flt_att_id = self.env['product.attribute.dte.wb'].search([('wb_dte_att_id','=',attribute_id.id),('wb_dte_mag_web_id','=',instance.id),
                    ('wb_dte_att_opt','=',str(attributes_odoo.get('value'))),('wb_dte_att_idc','=',product_ids.id),('wb_dte_mag_web_id','=',website_id.id)])
                    if not wb_flt_att_id:
                        wb_txt_att_id = self.env['product.attribute.dte.wb'].create({'wb_dte_att_id':attribute_id.id,'wb_dte_mag_web_id':instance.id,
                        'wb_dte_att_opt':str(attributes_odoo.get('value')),'wb_dte_att_idc':product_ids.id,'wb_dte_mag_web_id':website_id.id})
                elif attribute_id.scope == 'store':
                    sw_flt_att_id = self.env['product.attribute.dte.sw'].search([('sw_dte_att_id','=',attribute_id.id),('sw_dte_mag_inst_id','=',instance.id),
                    ('sw_dte_att_opt','=',str(attributes_odoo.get('value'))),('sw_dte_att_idc','=',product_ids.id),('sw_dte_mag_str_id','=',store_id.id)])
                    if not sw_flt_att_id:
                        sw_flt_att_id = self.env['product.attribute.dte.sw'].create({'sw_dte_att_id':attribute_id.id,'sw_dte_mag_inst_id':instance.id,
                        'sw_dte_att_opt':str(attributes_odoo.get('value')),'sw_dte_att_idc':product_ids.id,'sw_dte_mag_str_id':store_id.id})
        return True

    def GtExportMagentoProducts(self):
        multi_instance = self.env['gt.magento.product.multi']
        select_website = self.env["product.attribute.selection.wb"]
        select_store = self.env["product.attribute.selection.sw"]
        attribute_obj =self.env['gt.product.attributes']    
        if self.product_type == 'simple':
            for instance_id in self.magento_instance_ids:
                instance_id.generate_token()
                token=instance_id.token
                token=token.replace('"'," ")
                auth_token="Bearer "+token.strip()
                auth_token=auth_token.replace("'",'"')
                headers = {
                    'authorization':auth_token,
                    'content-type': "application/json",
                    'cache-control': "no-cache",
                    }
                for website_id in self.website_ids:
                    if instance_id == website_id.magento_instance_id:
                        for store_id in self.store_ids:
                            if store_id.website_id == website_id:
                                custom_options = self.create_simple_product_vals(store_id,instance_id)
                                status = ''
                                visibility = ''
                                status_id = attribute_obj.search([('attribute_code','=','status'),('referential_id','=',instance_id.id)])
                                if status_id:
                                    select_website_id = select_website.search([('wb_sel_att_id','=',status_id.id),('wb_sel_att_idc','=',self.id),('wb_sel_mag_web_id','=',website_id.id),('wb_sel_mag_inst_id','=',instance_id.id)])
                                    if select_website_id:
                                        status = select_website_id.wb_sel_att_opt_id.value
                                visibility_id = attribute_obj.search([('attribute_code','=','visibility'),('referential_id','=',instance_id.id)])
                                if visibility_id:
                                    select_store_id = select_store.search([('sw_sel_att_id','=',visibility_id.id),('sw_sel_att_idc','=',self.id),('sw_sel_mag_str_id','=',store_id.id),('sw_sel_mag_inst_id','=',instance_id.id)])
                                    if select_store_id:
                                        visibility = select_store_id.sw_sel_att_opt_id.value
                                vals =  {
                                    "product": {
                                        "id": 0,
                                        "sku": str(self.default_code),
                                        "name": str(self.name),
                                        "attributeSetId": 4,
                                        "price": self.lst_price,
                                        "status":  status or 1,
                                        "visibility": visibility or 4,
                                        "type_id":str(self.product_type),
                                        #"tierPrices":tier_price,
                                        #"customAttributes":custom_options,
                                    }
                                }
                                url=str(instance_id.location)+"/rest/V1/products/"
                                productload= str(vals) 
                                productload=productload.replace("'",'"')  
                                productload=str(productload)
                                response = requests.request("POST",url,data=productload, headers=headers)
                                if str(response.status_code)=="200":
                                    each_response=json.loads(response.text)
                                    product_id = multi_instance.search([('magento_id','=',each_response['id']),('gt_magento_instance_id','=',instance_id.id),('gt_magento_exported','=',True),('product_id','=',self.id)])
                                    if not product_id:
                                        product_id = multi_instance.create({'magento_id':each_response['id'],'gt_magento_instance_id':instance_id.id,'gt_magento_exported':True,'product_id':self.id})
                                    prods_id = []
                                    for prod_id in self.gt_magento_product_ids:
                                        prods_id.append(prod_id.id)
                                    if product_id.id not in prods_id:
                                        prods_id.append(product_id.id)
                                    self.write({'gt_magento_product_ids':[(6,0,prods_id)]})
            self.write({'exported_magento':True})
            self._cr.commit()
        return True

    def create_simple_product_vals(self,store_id,instance_id):
        select_global = self.env["product.attribute.selection.gl"]
        select_website = self.env["product.attribute.selection.wb"]
        select_store = self.env["product.attribute.selection.sw"]
        
        multi_global = self.env["product.attribute.multiselect.gl"]
        multi_website = self.env["product.attribute.multiselect.wb"]
        multi_store = self.env["product.attribute.multiselect.sw"]
        
        text_global = self.env["product.attribute.txt.gl"]
        text_website = self.env["product.attribute.txt.wb"]
        text_store = self.env["product.attribute.txt.sw"]
        
        float_global = self.env["product.attribute.flt.gl"]
        float_website = self.env["product.attribute.flt.wb"]
        float_store = self.env["product.attribute.flt.sw"]
        
        date_global = self.env["product.attribute.dte.gl"]
        date_website = self.env["product.attribute.dte.wb"]
        date_store = self.env["product.attribute.dte.sw"]
        
        ml_gl = []
        ml_wb = []
        ml_sw = []
        custom_options = []
        tier_price = []
        categ = []
        option_value = []
        select_global_ids = select_global.search([('gl_sel_att_idc','=',self.id),('gl_sel_mag_inst_id','=',instance_id.id)])
        for glb_ids in select_global_ids:
            custom_options.append({"attributeCode":str(glb_ids.gl_sel_att_id.attribute_code),"value":str(glb_ids.gl_sel_att_opt_id.value)})
        multi_global_ids = multi_global.search([('gl_mul_att_idc','=',self.id),('gl_mul_mag_inst_id','=',instance_id.id)])
        for multi_ids in multi_global_ids:
            for option in multi_ids.gl_mul_att_opt_id:
                ml_gl.append(option.value)
            custom_options.append({"attributeCode":str(multi_ids.gl_mul_att_id.attribute_code),"value":ml_gl})
        text_global_ids = text_global.search([('gl_txt_att_idc','=',self.id),('gl_txt_mag_inst_id','=',instance_id.id)])
        for tx_ids in text_global_ids:
            custom_options.append({"attributeCode":str(tx_ids.gl_txt_att_id.attribute_code),"value":str(tx_ids.gl_txt_att_opt)})
        float_global_ids = float_global.search([('gl_flt_att_idc','=',self.id),('gl_flt_mag_inst_id','=',instance_id.id)])
        for fl_ids in float_global_ids:
            custom_options.append({"attributeCode":str(fl_ids.gl_flt_att_id.attribute_code),"value":str(fl_ids.gl_flt_att_opt)})
        date_global_ids = date_global.search([('gl_dte_att_idc','=',self.id),('gl_dte_mag_inst_id','=',instance_id.id)])
        for dt_ids in date_global_ids:
            custom_options.append({"attributeCode":str(dt_ids.gl_dte_att_id.attribute_code),"value":str(dt_ids.gl_dte_att_opt)})
        
        select_website_ids = select_website.search([('wb_sel_att_idc','=',self.id),('wb_sel_mag_inst_id','=',instance_id.id),('wb_sel_mag_web_id','=',store_id.website_id.id)])
        for gl_wb_ids in select_website_ids:
            custom_options.append({"attributeCode":str(gl_wb_ids.wb_sel_att_id.attribute_code),"value":str(gl_wb_ids.wb_sel_att_opt_id.value)})
        multi_website_ids = multi_website.search([('wb_mul_att_idc','=',self.id),('wb_mul_mag_inst_id','=',instance_id.id),('wb_mul_mag_web_id','=',store_id.website_id.id)])
        for ml_wb_ids in multi_website_ids:
            for option in ml_wb_ids.wb_mul_att_opt_id:
                ml_wb.append(option.value)
            custom_options.append({"attributeCode":str(ml_wb_ids.wb_mul_att_id.attribute_code),"value":ml_wb})
        text_website_ids = text_website.search([('wb_txt_att_idc','=',self.id),('wb_txt_mag_inst_id','=',instance_id.id),('wb_txt_mag_web_id','=',store_id.website_id.id)])
        for tx_wb_ids in text_website_ids:
            custom_options.append({"attributeCode":str(tx_wb_ids.wb_txt_att_id.attribute_code),"value":str(tx_wb_ids.wb_txt_att_opt)})
        float_website_ids = float_website.search([('wb_flt_att_idc','=',self.id),('wb_flt_mag_inst_id','=',instance_id.id),('wb_flt_mag_web_id','=',store_id.website_id.id)])
        for fl_wb_ids in float_website_ids:
            custom_options.append({"attributeCode":str(fl_wb_ids.wb_flt_att_id.attribute_code),"value":str(fl_wb_ids.wb_flt_att_opt)})
        date_website_ids = date_website.search([('wb_dte_att_idc','=',self.id),('wb_dte_mag_inst_id','=',instance_id.id),('wb_dte_mag_web_id','=',store_id.website_id.id)])
        for dt_wb_ids in date_website_ids:
            custom_options.append({"attributeCode":str(dt_wb_ids.wb_dte_att_id.attribute_code),"value":str(dt_wb_ids.wb_dte_att_opt)})
        
        select_store_ids = select_store.search([('sw_sel_att_idc','=',self.id),('sw_sel_mag_inst_id','=',instance_id.id),('sw_sel_mag_str_id','=',store_id.id)])
        for gl_sw_ids in select_store_ids:
            custom_options.append({"attributeCode":str(gl_sw_ids.sw_sel_att_id.attribute_code),"value":str(gl_sw_ids.sw_sel_att_opt_id.value)})
        multi_store_ids = multi_store.search([('sw_mul_att_idc','=',self.id),('sw_mul_mag_inst_id','=',instance_id.id),('sw_mul_mag_str_id','=',store_id.id)])
        for ml_sw_ids in multi_store_ids:
            for option in ml_sw_ids.sw_mul_att_opt_id:
                ml_sw.append(option.value)
            custom_options.append({"attributeCode":str(ml_sw_ids.sw_mul_att_id.attribute_code),"value":ml_sw})
        text_store_ids = text_store.search([('sw_txt_att_idc','=',self.id),('sw_txt_mag_inst_id','=',instance_id.id),('sw_txt_mag_str_id','=',store_id.id)])
        for tx_sw_ids in text_store_ids:
            custom_options.append({"attributeCode":str(tx_sw_ids.sw_txt_att_id.attribute_code),"value":str(tx_sw_ids.sw_txt_att_opt)})
        float_store_ids = float_store.search([('sw_flt_att_idc','=',self.id),('sw_flt_mag_inst_id','=',instance_id.id),('sw_flt_mag_str_id','=',store_id.id)])
        for fl_sw_ids in float_store_ids:
            custom_options.append({"attributeCode":str(fl_sw_ids.sw_flt_att_id.attribute_code),"value":str(fl_sw_ids.sw_flt_att_opt)})
        date_store_ids = date_store.search([('sw_dte_att_idc','=',self.id),('sw_dte_mag_inst_id','=',instance_id.id),('sw_dte_mag_str_id','=',store_id.website_id.id)])
        for dt_sw_ids in date_store_ids:
            custom_options.append({"attributeCode":str(dt_sw_ids.sw_dte_att_id.attribute_code),"value":str(dt_sw_ids.sw_dte_att_opt)})
        #print ('custom_options+++++++++++',custom_options)
        for category in  self.prod_category_id:
            if instance_id == category.magento_instance_id:
                categ.append(category.magento_id)
        if categ:
            custom_options.append({"attributeCode":'category_ids',"value":categ})
        return custom_options

    def GtUpdateMagentoProducts(self):
        select_website = self.env["product.attribute.selection.wb"]
        select_store = self.env["product.attribute.selection.sw"]
        multi_ids = self.env['gt.magento.product.multi']
        attribute_obj =self.env['gt.product.attributes']
        try:
            if self.product_type == 'simple':
                for instance_id in self.magento_instance_ids:
                    instance_id.generate_token()
                    token=instance_id.token
                    token=token.replace('"'," ")
                    auth_token="Bearer "+token.strip()
                    auth_token=auth_token.replace("'",'"')
                    headers = {
                        'authorization':auth_token,
                        'content-type': "application/json",
                        'cache-control': "no-cache",
                    }
                    for website_id in self.website_ids:
                        if instance_id == website_id.magento_instance_id:
                            for store_id in self.store_ids:
                                if store_id.website_id == website_id:
                                    custom_options = self.create_simple_product_vals(store_id,instance_id)
                                    status = ''
                                    visibility = ''
                                    status_id = attribute_obj.search([('attribute_code','=','status'),('referential_id','=',instance_id.id)])
                                    if status_id:
                                        select_website_id = select_website.search([('wb_sel_att_id','=',status_id.id),('wb_sel_att_idc','=',self.id),('wb_sel_mag_web_id','=',website_id.id),('wb_sel_mag_inst_id','=',instance_id.id)])
                                        if select_website_id:
                                            status = select_website_id.wb_sel_att_opt_id.value
                                    visibility_id = attribute_obj.search([('attribute_code','=','visibility'),('referential_id','=',instance_id.id)])
                                    if visibility_id:
                                        select_store_id = select_store.search([('sw_sel_att_id','=',visibility_id.id),('sw_sel_att_idc','=',self.id),('sw_sel_mag_str_id','=',store_id.id),('sw_sel_mag_inst_id','=',instance_id.id)])
                                        if select_store_id:
                                            visibility = select_store_id.sw_sel_att_opt_id.value
                                    multi_id = multi_ids.search([('gt_magento_instance_id','=',instance_id.id),('gt_magento_exported','=',True),('product_id','=',self.id)])
                                    if multi_id:
                                        vals =  {
                                            "product": {
                                                "id": str(multi_id.magento_id),
                                                "sku": str(self.default_code),
                                                "name": str(self.name),
                                                "attributeSetId": self.attribute_set.code,
                                                "price": self.lst_price,
                                                "status": status or 1,
                                                "visibility": visibility or 4,
                                                "type_id":str(self.product_type),
                                                #"tierPrices":tier_price,
                                                "customAttributes":custom_options,
                                            }
                                        }
                                        print ("*==> Update value of product :: ",vals)
                                        url=str(instance_id.location)+"rest/"+ str(store_id.code) +"/V1/products/"+str(self.default_code)
                                        productload= str(vals) 
                                        productload=productload.replace("'",'"')  
                                        productload=str(productload)
                                        response = requests.request("PUT",url,data=productload, headers=headers)
                                        each_response=json.loads(response.text)
                                    self._cr.commit()
        except Exception as e:
            print ("*=======> Error <======= %s",e)
        return True
    
    def GtExportSingleProductStock(self):
        for instance_id in self.magento_instance_ids:
            instance_id.generate_token()
            token=instance_id.token
            token=token.replace('"'," ")
            auth_token="Bearer "+token.strip()
            auth_token=auth_token.replace("'",'"')
            headers = {
                'authorization':auth_token,
                'content-type': "application/json",
                'cache-control': "no-cache",
            }
            if self.qty_available >= 0.00:
                vals = { "sourceItems": []}
                for store in self.store_ids:
                    data = {
                    "sku": self.default_code,
                    "source_code": store.source_code,
                    "quantity": self.env['stock.quant']._get_available_quantity(self,store.warehouse_id.lot_stock_id),
                    "status": 1
                    }
                    vals['sourceItems'].append(data)
                payload = str(vals) 
                payload=payload.replace("'",'"')     
                payload=str(payload)
                if self.store_ids and self.store_ids[0].code:
                    store_code = self.store_ids[0].code
                else:
                    store_code = "default2"
                url=instance_id.location+"rest/"+store_code+"/V1/inventory/source-items"
                response = requests.request("PUT",url, data=payload, headers=headers)
                if str(response.status_code)=="200":
                    each_response=json.loads(response.text)
                _logger.info(response.text)
        return True
    
    def magento_export_stock(self):
        _logger.info('cron export stock start')
        products = self.env['product.product'].search([('state','not in',('low','draft'))])
        for product in products:
            product.GtExportSingleProductStock()
        _logger.info('cron export stock end')
#######################OLD IMAGE EXPORT CODE####################    
    # def GtExportMagentoProductImage(self):
    #     multi_instance = self.env['gt.magento.product.image.multi']
    #     for lst_image in self.product_image_id:
    #         for instance in lst_image.magento_instance_ids:
    #             lst_image.write({'is_exported':False})
    #             instance.generate_token()
    #             token=instance.token
    #             token=token.replace('"'," ")
    #             auth_token1="Bearer "+token.strip()
    #             auth_token=auth_token1.replace("'",'"')
    #             headers = {
    #                 'authorization':auth_token,
    #                 'content-type': "application/json",
    #                 'cache-control': "no-cache",
    #                 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    #                 }  
    #             if lst_image.is_exported == False:
    #                 #decodes = c.decode("base64")
    #                 decodes = base64.b64decode(lst_image.image)
    #                 #newdecode = decodes.encode("base64")
    #                 newdecode = base64.b64encode(decodes)
    #                 type_image = []
    #                 if lst_image.small_image == True:
    #                     type_image.append('image')
    #                 if lst_image.thumbnail == True:
    #                     type_image.append('thumbnail')
    #                 if lst_image.swatch_image == True:
    #                     type_image.append('swatch_image')
    #                 if lst_image.base_image == True:
    #                     type_image.append('image')
    #                 vals ={
    #                     "entry": {
    #                         "media_type": "image",
    #                         "position": 1,
    #                         "disabled": "false",
    #                         "types": type_image,
    #                         "label":"testimage",
    #                         "content":{
    #                           "base64_encoded_data" : newdecode,
    #                           "type": "image/"+ str(lst_image.image_extension),
    #                           "name": str(lst_image.name),
    #                       }
    #                     }
    #                   }
    #                 print ("vals+9++++++++++++++",vals)
    #                 url=str(instance.location)+"rest/V1/products/"+str(self.default_code)+"/media"
    #                 print ("url++++++++++++",url)
    #                 productload= str(vals) 
    #                 productload=productload.replace("'",'"')  
    #                 productload=str(productload)
    #                 response = requests.request("POST",url,data=productload, headers=headers)
    #                 print ("response+++++++++++++++++",response)
    #                 print ('response.status_code++++++',response.status_code)
    #                 print ("json.loads(response.text)++++++++++++",json.loads(response.text))
    #                 if str(response.status_code)=="200":
    #                     each_response=json.loads(response.text)
    #                     product_id = multi_instance.search([('magento_id','=',each_response['id']),('gt_magento_instance_id','=',instance.id),('gt_magento_exported','=',True),('images_ids','=',lst_image.id)])
    #                     if not product_id:
    #                         product_id = multi_instance.create({'magento_id':each_response['id'],'gt_magento_instance_id':instance.id,'gt_magento_exported':True,'images_ids':lst_image.id})
    #                     prods_id = []
    #                     for prod_id in lst_image.gt_magento_image_ids:
    #                         prods_id.append(prod_id.id)
    #                     if product_id.id not in prods_id:
    #                         prods_id.append(product_id.id)
    #                     self.write({'gt_magento_image_ids':[(6,0,prods_id)]})
    #                     lst_image.write({'is_exported':True})
    #     return True

##############NEW EXPORT IMAGE CODE UPDATED BY TUSHAR##################

    def GtExportMagentoProductImage(self):
        multi_instance = self.env['gt.magento.product.image.multi']
        for lst_image in self.product_image_id:
            print("<><><><><><><><><>LST_IMAGE<><><><><><><>", lst_image)
            for instance in lst_image.magento_instance_ids:
                lst_image.write({'is_exported':False})
                instance.generate_token()
                token=instance.token
                token=token.replace('"'," ")
                auth_token1="Bearer "+token.strip()
                auth_token=auth_token1.replace("'",'"')
                headers = {
                    'authorization':auth_token,
                    'content-type': "application/json",
                    'cache-control': "no-cache",
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
                    }  
                if lst_image.is_exported == False:
                    # with open('/home/tushar/Downloads/test_image.jpeg', "rb") as image_file:
                    #     b64_encoded_string = base64.b64encode(image_file.read()).decode("utf8")
                    # raw_data = {'base64_encoded_data': b64_encoded_string, 'type': 'image/jpeg', 'name': 'test_image.jpeg'}
                    # json_data = dumps(raw_data, indent=2)
                    #decodes = c.decode("base64")
                    decodes = base64.b64decode(lst_image.image)
                    #newdecode = decodes.encode("base64")
                    newdecode = (base64.b64encode(decodes)).decode("utf8")
                    print("<><><><><>><NEWCXOD?????????????", type(newdecode))
                    type_image = []
                    if lst_image.small_image == True:
                        type_image.append('image')
                    if lst_image.thumbnail == True:
                        type_image.append('thumbnail')
                    if lst_image.swatch_image == True:
                        type_image.append('swatch_image')
                    if lst_image.base_image == True:
                        type_image.append('image')
                    vals ={
                        "entry": {
                            "media_type": "image",
                            "position": 1,
                            "disabled": "true",
                            "types": type_image,
                            "label":"testimage",
                            "content":{
                              "base64_encoded_data" : newdecode,
                              "type": "image/"+ str(lst_image.image_extension),
                              "name": str(lst_image.name),
                          }
                        }
                      }
                    print ("*==> VALS:: ",vals)
                    url=str(instance.location)+"rest/V1/products/"+str(self.default_code)+"/media"
                    print ("*==> URL::",url)
                    productload= str(vals)
                    productload=productload.replace("'",'"')
                    productload=str(productload)
                    response = requests.request("POST",url,data=productload, headers=headers)
                    # print ("productload+++++++++++++++++",productload)
                    print ('*==> RESPONSE.STATUS_CODE:: ',response.status_code)
                    # print ("json.loads(response.text)++++++++++++",json.loads(response.text))
                    if str(response.status_code)=="200":
                        each_response=json.loads(response.text)
                        print("<><><><><>>ECH///////////////", each_response)
                        product_id = multi_instance.search([('magento_id','=',each_response),('gt_magento_instance_id','=',instance.id),('gt_magento_exported','=',True),('images_ids','=',lst_image.id)])
                        if not product_id:
                            product_id = multi_instance.create({'magento_id':each_response,'gt_magento_instance_id':instance.id,'gt_magento_exported':True,'images_ids':lst_image.id})
                            # print("++++++++++++++++++PROD++++++++++++", product_id, product_id.gt_magento_image_ids)
                        prods_id = []
                        for prod_id in lst_image.gt_magento_image_ids:
                            print("+++=========================iddddd", prod_id)
                            prods_id.append(prod_id.id)
                        if product_id.id not in prods_id:
                            # print("++++++++++++++++++PROD++++++++++++", product_id)
                            prods_id.append(product_id.id)
                        lst_image.write({'gt_magento_image_ids':[(6,0,prods_id)]})
                        lst_image.write({'is_exported':True})
        return True


class ProductAttributeSelectionGL(models.Model):
    _name="product.attribute.selection.gl"
    _description = 'Magento Store Selection Attribute Global'
    
    gl_sel_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    gl_sel_att_opt_id = fields.Many2one('gt.product.attribute.options', string='Attribute Option', domain="[('attribute_id','=',gl_sel_att_id)]")
    gl_sel_att_idc = fields.Many2one('product.product', string='Product Variant')
    gl_sel_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)

class ProductAttributeSelectionWB(models.Model):
    _name="product.attribute.selection.wb"
    _description = 'Magento Store Selection Attribute Website'
    
    @api.onchange('wb_sel_mag_web_id')
    def onchange_wb_sel_mag_inst_id(self):
        self.wb_sel_mag_inst_id = self.wb_sel_mag_web_id.magento_instance_id
    
    wb_sel_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    wb_sel_att_opt_id = fields.Many2one('gt.product.attribute.options', string='Attribute Option', domain="[('attribute_id','=',wb_sel_att_id)]")
    wb_sel_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    wb_sel_mag_web_id = fields.Many2one('gt.magento.website', string='Magento Website', track_visibility='onchange')
    wb_sel_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    
    
    
class ProductAttributeSelectionWB(models.Model):
    _name="product.attribute.selection.sw"
    _description = 'Magento Store Selection Attribute Store'
    
    @api.onchange('sw_sel_mag_str_id')
    def onchange_sw_sel_mag_inst_id(self):
        self.sw_sel_mag_inst_id = self.sw_sel_mag_str_id.magento_instance_id
    
    
    sw_sel_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    sw_sel_att_opt_id = fields.Many2one('gt.product.attribute.options', string='Attribute Option', domain="[('attribute_id','=',sw_sel_att_id)]")
    sw_sel_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    sw_sel_mag_str_id = fields.Many2one('gt.magento.store', string='Magento Store')
    sw_sel_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)


class ProductAttributeMultiSelectGL(models.Model):
    _name="product.attribute.multiselect.gl"
    _description = 'Magento Store Multiselect Attribute Global' 
    
    
    gl_mul_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    gl_mul_att_opt_id = fields.Many2many('gt.product.attribute.options','att_op_rel_gl','opt_id_gl','att_id_gl', string='Attribute Option', domain="[('attribute_id','=',gl_mul_att_id)]")
    gl_mul_att_idc = fields.Many2one('product.product', string='Product Variant')
    gl_mul_mag_inst_id = fields.Many2one('gt.magento.instance', stirng='Magento Instance', store=True)

class ProductAttributeMultiSelectWB(models.Model):
    _name="product.attribute.multiselect.wb"
    _description = 'Magento Store Multiselect Attribute Website'
    
    @api.onchange('wb_mul_mag_web_id')
    def onchange_wb_mul_mag_inst_id(self):
        self.wb_mul_mag_inst_id = self.wb_mul_mag_web_id.magento_instance_id
    
    wb_mul_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    wb_mul_att_opt_id = fields.Many2many('gt.product.attribute.options','att_op_rel_wb','opt_id_wb','att_id_wb', string='Attribute Option', domain="[('attribute_id','=',wb_mul_att_id)]")
    wb_mul_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    wb_mul_mag_web_id = fields.Many2one('gt.magento.website', string='Magento Website')
    wb_mul_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    
    
class ProductAttributeMultiSelectSB(models.Model):
    _name="product.attribute.multiselect.sw"
    _description = 'Magento Store Multiselect Attribute Store'
    
    @api.onchange('sw_mul_mag_str_id')
    def onchange_sw_mul_mag_inst_id(self):
        self.sw_mul_mag_inst_id = self.sw_mul_mag_str_id.magento_instance_id
    
    
    sw_mul_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    sw_mul_att_opt_id = fields.Many2many('gt.product.attribute.options','att_op_rel_sw','opt_id_sw','att_id_sw', string='Attribute Option', domain="[('attribute_id','=',sw_mul_att_id)]")
    sw_mul_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    sw_mul_mag_str_id = fields.Many2one('gt.magento.store', string='Magento Store')
    sw_mul_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)


class ProductAttributeTxtGL(models.Model):
    _name="product.attribute.txt.gl"
    _description = 'Magento Store Text Attribute Global'
    
    
    gl_txt_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    gl_txt_att_opt = fields.Text(string='Attribute Value')
    gl_txt_att_idc = fields.Many2one('product.product', string='Product Variant')
    gl_txt_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)

class ProductAttributeTxtWB(models.Model):
    _name="product.attribute.txt.wb"
    _description = 'Magento Store Text Attribute Website'
    
    @api.onchange('wb_txt_mag_web_id')
    def onchange_wb_txt_mag_inst_id(self):
        self.wb_txt_mag_inst_id = self.wb_txt_mag_web_id.magento_instance_id
    
    wb_txt_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    wb_txt_att_opt = fields.Text(string='Attribute Value')
    wb_txt_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    wb_txt_mag_web_id = fields.Many2one('gt.magento.website', string='Magento Website')
    wb_txt_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    
class ProductAttributeTxtWB(models.Model):
    _name="product.attribute.txt.sw"
    _description = 'Magento Store Text Attribute Store'
    
    @api.onchange('sw_txt_mag_str_id')
    def onchange_sw_txt_mag_inst_id(self):
        self.sw_txt_mag_inst_id = self.sw_txt_mag_str_id.magento_instance_id
    
    sw_txt_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    sw_txt_att_opt = fields.Text(string='Attribute Value')
    sw_txt_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    sw_txt_mag_str_id = fields.Many2one('gt.magento.store', string='Magento Store')
    sw_txt_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)


class ProductAttributeFltGL(models.Model):
    _name="product.attribute.flt.gl"
    _description = 'Magento Store Float Attribute Global'
    
    
    gl_flt_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    gl_flt_att_opt = fields.Float(string='Attribute Value')
    gl_flt_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    gl_flt_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)

class ProductAttributeFltWB(models.Model):
    _name="product.attribute.flt.wb"
    _description = 'Magento Store Float Attribute Website'
    
    @api.onchange('wb_flt_mag_web_id')
    def onchange_wb_flt_mag_inst_id(self):
        self.wb_flt_mag_inst_id = self.wb_flt_mag_web_id.magento_instance_id
    
    wb_flt_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    wb_flt_att_opt = fields.Float(string='Attribute Value')
    wb_flt_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    wb_flt_mag_web_id = fields.Many2one('gt.magento.website', string='Magento Website')
    wb_flt_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    
class ProductAttributeFltWB(models.Model):
    _name="product.attribute.flt.sw"
    _description = 'Magento Store Float Attribute Store'
    
    @api.onchange('sw_flt_mag_str_id')
    def onchange_sw_flt_mag_inst_id(self):
        self.sw_flt_mag_inst_id = self.sw_flt_mag_str_id.magento_instance_id
    
    sw_flt_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    sw_flt_att_opt = fields.Float(string='Attribute Value')
    sw_flt_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    sw_flt_mag_str_id = fields.Many2one('gt.magento.store', string='Magento Store')
    sw_flt_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    
class ProductAttributeDteGL(models.Model):
    _name="product.attribute.dte.gl"
    _description = 'Magento Store Date Attribute Global'
    
    gl_dte_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    gl_dte_att_opt = fields.Date(string='Attribute Value')
    gl_dte_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    gl_dte_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)

class ProductAttributeDteWB(models.Model):
    _name="product.attribute.dte.wb"
    _description = 'Magento Store Date Attribute Website'
    
    @api.onchange('wb_dte_mag_web_id')
    def onchange_wb_dte_mag_inst_id(self):
        self.wb_dte_mag_inst_id = self.wb_dte_mag_web_id.magento_instance_id
    
    wb_dte_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    wb_dte_att_opt = fields.Date(string='Attribute Value')
    wb_dte_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    wb_dte_mag_web_id = fields.Many2one('gt.magento.website', string='Magento Website')
    wb_dte_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    
class ProductAttributeDteWB(models.Model):
    _name="product.attribute.dte.sw"
    _description = 'Magento Store Date Attribute Store'
    
    @api.onchange('sw_dte_mag_str_id')
    def onchange_sw_dte_mag_inst_id(self):
        self.sw_dte_mag_inst_id = self.sw_dte_mag_str_id.magento_instance_id

    sw_dte_att_id = fields.Many2one('gt.product.attributes', string='Attribute')
    sw_dte_att_opt = fields.Date(string='Attribute Value')
    sw_dte_att_idc = fields.Many2one('product.product', string= 'Product Variant')
    sw_dte_mag_str_id = fields.Many2one('gt.magento.store', string='Magento Store')
    sw_dte_mag_inst_id = fields.Many2one('gt.magento.instance', string='Magento Instance', store=True)
    

class GtMagentoProductMulti(models.Model):
    _name = 'gt.magento.product.multi'
    _description = 'Magento Product ID Multi'
    _rec_name = 'magento_id'
    
    
    magento_id = fields.Char(string='Product ID')
    gt_magento_instance_id = fields.Many2one('gt.magento.instance', string='Shopify Instance')
    gt_magento_exported = fields.Boolean(string='Shopify Exported')
    product_id = fields.Many2one('product.product', string="Product")
    
    
