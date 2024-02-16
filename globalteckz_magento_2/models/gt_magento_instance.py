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

from dbm import whichdb
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json
import urllib
import base64
import datetime
from datetime import date
import logging
logger = logging.getLogger('product')
import urllib.request
import re

_logger = logging.getLogger(__name__)

class SkuReferenceImport(models.Model):
    _name = 'sku.reference.import'
    _description = "SKU Reference Import"

    name = fields.Char(string='SKU')
    import_success = fields.Boolean('Import Success')

class GtMagentoInstance(models.Model):
    _name='gt.magento.instance'
    _description = "GT Magento Instance"
    _rec_name = "name"
    
    
    name = fields.Char(string='Name',size=64, required=True)
    location = fields.Char(string='Location',size=64,required=True)
    apiusername = fields.Char(string='User Name',size=64,required=True)
    apipassoword = fields.Char(string='Password',size=64,required=True)
    token=fields.Char(string='Token')
    location_id = fields.Many2one('stock.location',string='Stock Location')
    count_magento_shop = fields.Integer(compute='GetShopCount')
    count_magento_websites = fields.Integer(compute='GetWebsiteCount')
    count_magento_attribute_set = fields.Integer(compute='GetAttributeSetCount')
    count_magento_attributes = fields.Integer(compute='GetAttributesCount')
    count_magento_categories = fields.Integer(compute='GetCategoriesCount')
    count_magento_products = fields.Integer(compute='GetProductsCount')
    count_magento_customers = fields.Integer(compute='GetCustomersCount')
    from_id = fields.Integer(string="Simple From ID", default=1)
    config_prod_from_id = fields.Integer(string="Config From ID", default=1)
    to_id = fields.Integer(string="Simple To ID", compute='_compute_simple_to_id')
    config_prod_to_id = fields.Integer(string="Config To ID", default=1, compute='_compute_configurable_to_id')
    cust_from_id = fields.Integer(string="Customer From ID", default=1)
    limit_simple_product_id = fields.Integer(string='Limit for Simple Product ID Import', default=1000)
    limit_configurable_product_id = fields.Integer(string='Limit for Configurable Product ID Import', default=1000)
    sku_reference_ids = fields.Many2many('sku.reference.import', string='Product Sku Reference Import')
    magento_instance_id_used_token = fields.Boolean('Used Token')

    @api.depends('from_id')
    def _compute_simple_to_id(self):
        for record in self:
            record.to_id = record.from_id + record.limit_simple_product_id
            
    @api.depends('config_prod_from_id')
    def _compute_configurable_to_id(self):
        for record in self:
            record.config_prod_to_id = record.config_prod_from_id + record.limit_configurable_product_id
            
    
    def ActionGetShop(self):
        magento_shop = self.env['gt.magento.store'].search([('magento_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_magento_2.gt_act_magento_shop')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': [('id', 'in', magento_shop.ids)]
        }

        return result
    
    def ActionGetWebsites(self):
        magento_web = self.env['gt.magento.website'].search([('magento_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_magento_2.gt_act_magento_website')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': [('id', 'in', magento_web.ids)]
        }

        return result
      
    def ActionGetAttributeSets(self):
        magento_att_set = self.env['gt.product.attribute.set'].search([('magento_instance_id','=',self.id)])
        action = self.env.ref('globalteckz_magento_2.act_gt_product_attribute_set')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': [('id', 'in', magento_att_set.ids)]
        }

        return result
      
    def ActionGetAttributes(self):
        magento_attributes = self.env['gt.product.attributes'].search([('referential_id','=',self.id)])
        action = self.env.ref('globalteckz_magento_2.act_gt_product_attributes')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': [('id', 'in', magento_attributes.ids)]
        }

        return result  
    
    def ActionGetCategories(self):
        magento_category = self.env['product.category'].search([('magento_instance_id','=',self.id)])
        action = self.env.ref('product.product_category_action_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': [('id', 'in', magento_category.ids)]
        }

        return result
    
    def ActionGetProduct(self):
        # magento_products = self.env['product.product'].search([('magento_instance_ids','in',self.id)])
        magento_products = self.env['product.template'].search([('magento_instance_ids','in',self.id)])
        action = self.env.ref('globalteckz_magento_2.act_magento_products')
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
    
    def ActionGetCustomer(self):
        magento_products = self.env['res.partner'].search([('magento_instance_ids','=',self.id)])
        action = self.env.ref('globalteckz_magento_2.action_magento_customer')
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
    
    def GetShopCount(self):
        shop_obj = self.env['gt.magento.store']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_instance_id', '=', shop.id)])
            shop.count_magento_shop = len(multishop_ids.ids)
        return res
       
    def GetWebsiteCount(self):
        shop_obj = self.env['gt.magento.website']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_instance_id', '=', shop.id)])
            shop.count_magento_websites = len(multishop_ids.ids)
        return res
       
    def GetAttributeSetCount(self):
        shop_obj = self.env['gt.product.attribute.set']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_instance_id', '=', shop.id)])
            shop.count_magento_attribute_set = len(multishop_ids.ids)
        return res
    
    def GetAttributesCount(self):
        shop_obj = self.env['gt.product.attributes']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('referential_id', '=', shop.id)])
            shop.count_magento_attributes = len(multishop_ids.ids)
        return res
         
    def GetCategoriesCount(self):
        shop_obj = self.env['product.category']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_instance_id', '=', shop.id)])
            shop.count_magento_categories = len(multishop_ids.ids)
        return res
    
    def GetProductsCount(self):
        shop_obj = self.env['product.template']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_instance_ids','in',self.id)])
            shop.count_magento_products = len(multishop_ids.ids)
        return res
     
    def GetCustomersCount(self):
        shop_obj = self.env['res.partner']
        res = {}
        for shop in self:
            multishop_ids = shop_obj.search([('magento_instance_ids','=',self.id)])
            shop.count_magento_customers = len(multishop_ids.ids)
        return res
    
    def generate_token(self):
        if not self.token:
            url=str(self.location)+"/rest/V1/integration/admin/token"
            payload = {"username":str(self.apiusername), "password":str(self.apipassoword)}
            headers = {'content-type': "application/json",'cache-control': "no-cache",}
            payload=str(payload)
            payload=payload.replace("'",'"')
            payload=str(payload)
            response = requests.request("POST",url, data=payload, headers=headers)
            if str(response.status_code)=="200":
                self.write({'token':json.loads(response.text)})
                self._cr.commit()
            else:
                raise UserError(_('Cant generate the token!'))
            return True
        else:
            return True

    def gt_create_magento_website(self):      
        website_obj = self.env['gt.magento.website']
        try:
            self.generate_token()
            url=self.location+"/rest/V1/store/websites"
            headers = {'authorization':"Bearer "+self.token}
            response = requests.request("GET",url, headers=headers)
            if str(response.status_code)=="200":
                websites=json.loads(response.text)
                for website in websites:
                    try:
                        if len(website):
                            website_id=website_obj.search([('code','=',website['code']),('magento_instance_id','=',self.id)])
                            if website['name'] != 'Admin':
                                if not website_id:
                                    website_obj.create({'name':website['name'],'code':website['code'],'magento_website':True,
                                    'website_id':website['id'], 'default_group_id':website['default_group_id'],'magento_instance_id':self.id })
                                else:
                                    website_id.write({'name':website['name'], 'code':website['code'],'website_id':website['id'], 
                                    'default_group_id':website['default_group_id'],'magento_instance_id':self.id,'magento_website':True,})
                            self._cr.commit()
                    except Exception as exc:
                        logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
        except Exception as exc:
            logger.error('*=========>  EXCEPTION <=========  ::  %s', exc)
        return True
    
    def gt_create_magento_stores(self):
        store_obj = self.env['gt.magento.store']
        website_obj = self.env['gt.magento.website']
        self.generate_token()
        url=self.location+"/rest/V1/store/storeViews"
        headers = {'authorization':"Bearer "+self.token}
        response = requests.request("GET",url, headers=headers)
        if str(response.status_code)=="200":
            stores=json.loads(response.text)
            for store in stores:
                if len(store):
                    store_id=store_obj.search([('name','=',store['name']),('code','=',store['code']),('store_id','=',store['id']),('magento_instance_id','=',self.id)])
                    if store['name'] != 'Admin':
                        website_id = website_obj.search([('website_id','=',store['website_id']),('magento_instance_id','=',self.id)])
                        if not len(website_id):
                            raise UserError(_(' Import Magento Website First'))
                        if not store_id:
                            store_obj.create({'name':store['name'],'code':store['code'],'store_id':store['id'], 
                            'website_id':website_id.id,'magento_shop':True, 'magento_instance_id':self.id })
                        else:
                            store_id.write({'name':store['name'], 'code':store['code'],'store_id':store['id'], 
                            'website_id':website_id.id,'magento_shop':True, 'magento_instance_id':self.id })
                    self._cr.commit()
        return True
    
    def GtCreateMagentoAttributeSet(self):
        if not self.count_magento_shop:
            raise UserError(_('Please Create Store!'))
        if not self.count_magento_websites:
            raise UserError(_('Please Create Website!'))

        prod_att_obj = self.env['product.attribute']
        attribute_set_obj=self.env['gt.product.attribute.set']
        shop_obj=self.env['gt.magento.store']
        try:
            self.generate_token()
            shop_id=shop_obj.search([('magento_instance_id','=',self.id)])
            if not shop_id:
                raise UserError(_('Please Create Store'))
            url=self.location+"/rest/V1/products/attribute-sets/sets/list?searchCriteria=0"
            headers = { 'authorization':"Bearer "+self.token}
            response = requests.request("GET",url, headers=headers)

            if str(response.status_code)=='200':
                try:
                    list_prods=response.json().get('items')
                    for list_prod in list_prods:
                        val={
                            'name':list_prod['attribute_set_name'],'code':list_prod['attribute_set_id'],
                            'sort_order':list_prod['sort_order'],'entity_type_id':list_prod['entity_type_id'],
                            'magento_instance_id': self.id,
                            }
                        attribute_id=attribute_set_obj.search([('code','=',list_prod['attribute_set_id']),
                        ('magento_instance_id','=',self.id)])
                        if attribute_id:
                            attribute_id.write(val)
                            print("*==> writing atribute set!")
                            
                        else:
                            print("*==> creating atribute set!")
                            attribute_id = attribute_set_obj.create(val)

                        odoo_att_vals={
                            'name':list_prod['attribute_set_name'],
                            'is_attribute_magento':True,
                            'attribute_set_magento_id':attribute_id.id,
                            }
                        odoo_attribute_id=prod_att_obj.search([('attribute_set_magento_id','=',attribute_id.id),('is_attribute_magento','=',True)])
                        if odoo_attribute_id: 
                            odoo_attribute_id.write(odoo_att_vals)
                        else:
                            odoo_attribute_id.create(odoo_att_vals)
                        
                        self._cr.commit()
                except Exception as exc:
                    logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
                    raise UserError(_(exc))  
        except Exception as exc:
            logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
            raise UserError(_(exc))

        return True
    
    def GtCreateMagentoAttributes(self):

        if not self.count_magento_shop:
            raise UserError(_('Please Create Store!'))
        if not self.count_magento_websites:
            raise UserError(_('Please Create Website!'))

        prod_att_obj = self.env['product.attribute']
        att_set_obj = self.env['gt.product.attribute.set']
        att_obj = self.env['gt.product.attributes']
        att_opt_obj = self.env['gt.product.attribute.options']
        try:
            self.generate_token()
            headers = { 'authorization':"Bearer "+self.token }
            att_ids = att_set_obj.search([('magento_instance_id','=',self.id),('attributes_import','=',False)])
            for att_id in att_ids:
                url=self.location+"/rest/V1/products/attribute-sets/"+str(att_id.code)+"/attributes"
                response = requests.request("GET",url, headers=headers)
                if str(response.status_code)=='200':
                    attribute_list= json.loads(response.text)
                    for jsonloads in attribute_list:
                        try:
                            url = self.location+"/rest/V1/products/attributes/"+str(jsonloads['attribute_code'])
                            response = requests.request("GET",url, headers=headers)
                            if str(response.status_code)=='200':
                                jsonload= json.loads(response.text)
                                if 'default_frontend_label' in jsonload:
                                        prod_att_obj_count = prod_att_obj.search([('name','=',jsonloads['default_frontend_label'])])
                                    
                                        odoo_att_vals = {
                                            'name': jsonload['default_frontend_label'] if not prod_att_obj_count else jsonload['default_frontend_label'] + ' 2' ,
                                            'is_attribute_magento':True,
                                            'attribute_magento_id': jsonload['attribute_id'],
                                        }

                                        att_obj_id = att_obj.search([('attribute_code','=',jsonloads['attribute_code'])])

                                        if not att_obj_id:
                                            
                                            odoo_attr_id = prod_att_obj.create(odoo_att_vals)
                                            print("*==> creating atribute in odoo!")
                                            self._cr.commit()

                                            vals = {
                                                'attribute_code':jsonload['attribute_code'],
                                                'referential_id':self.id,
                                                'frontend_label':jsonload['default_frontend_label'],
                                                'is_searchable' : jsonload['is_searchable'] if 'is_searchable' in jsonload else False,
                                                'is_visible':jsonload['is_visible'] if 'is_visible' in jsonload else False,
                                                'is_visible_on_front':jsonload['is_visible_on_front'] if 'is_visible_on_front' in jsonload else False,
                                                'is_filterable':jsonload['is_filterable'] if 'is_filterable' in jsonload else False,
                                                'scope':jsonload['scope'] if 'scope' in jsonload else '',
                                                'magento_id':jsonload['attribute_id'],
                                                'is_unique':jsonload['is_unique'] if 'is_unique' in jsonload else False,
                                                'is_required':jsonload['is_required'] if 'is_required' in jsonload else False,
                                                'is_user_defined':jsonload['is_user_defined']if 'is_user_defined' in jsonload else False,
                                                'odoo_attr_id': odoo_attr_id.id,
                                            }

                                            attribute_oe_ids = att_obj.create(vals)
                                            print("*==> creating atribute in magento!")
                                            self._cr.commit()

                                            if len(jsonload['options']):
                                                for attribute_option in jsonload['options']:
                                                    if attribute_option['value']:
                                                        attribute_oe_opt_ids = att_opt_obj.search([('attribute_id','=',attribute_oe_ids.id),('value', '=', attribute_option['value'])])
                                                        if not attribute_oe_opt_ids:

                                                            attr_value_id = self.env['product.attribute.value'].search([('name', '=', attribute_option['label']), ('attribute_id', '=', odoo_attr_id.id)])

                                                            if not attr_value_id:
                                                                vals_odoo_attr_value = {
                                                                    'name': attribute_option['label'],
                                                                    'attribute_id':odoo_attr_id.id,
                                                                }
                                                                product_attr_value_id = self.env['product.attribute.value'].create(vals_odoo_attr_value)
                                                                self._cr.commit()

                                                                vals = {
                                                                    'attribute_id': attribute_oe_ids.id,
                                                                    'referential_id': self.id,
                                                                    'value': attribute_option['value'],
                                                                    'label': attribute_option['label'],
                                                                    'product_attr_value': product_attr_value_id.id,
                                                                }

                                                                att_opt_obj.create(vals)
                                                                print("*==> creating value of atribute in magento!")
                                                                self._cr.commit()

                                                        else:
                                                            attribute_oe_opt_ids.write(vals)
                                                            print("*==> updating value of atribute in magento!")
                                                        self._cr.commit()
                                        
                                        else:
                                            att_vals = {
                                                'name': jsonload['default_frontend_label'],
                                            }

                                            att_obj_id.odoo_attr_id.update(att_vals)

                                            vals = {
                                                'frontend_label':jsonload['default_frontend_label'],
                                                'is_searchable' : jsonload['is_searchable'] if 'is_searchable' in jsonload else False,
                                                'is_visible':jsonload['is_visible'] if 'is_visible' in jsonload else False,
                                                'is_required':jsonload['is_required'] if 'is_required' in jsonload else False,
                                                'is_user_defined':jsonload['is_user_defined']if 'is_user_defined' in jsonload else False,
                                            }

                                            attribute_oe_ids = att_obj_id.update(vals)

                        except Exception as exc:
                            logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
                            pass
        except Exception as exc:
            logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
            pass
        return True
    
    def GtImportMagentoCategories(self):
        if not self.count_magento_shop:
            raise UserError(_('Please Create Store!'))
        if not self.count_magento_websites:
            raise UserError(_('Please Create Website!'))

        category_obj = self.env['product.category']
        magento_shop = self.env['gt.magento.store']
        try:
            self.generate_token()
            store_ids = magento_shop.search([('magento_instance_id','=',self.id)])
            for shop in store_ids:
                url=self.location+"/rest/"+str(shop.code)+"/V1/categories/"
                headers = {'authorization':"Bearer "+self.token }
                response = requests.request("GET",url, headers=headers)
                if str(response.status_code)=='200':
                    try:
                        if response.json().get('is_active')==True:
                            if str(response.json().get('parent_id'))=="1" or str(response.json().get('parent_id'))=="0":
                                category_id=category_obj.search([('name','=',response.json().get('name')),('magento_id','=',response.json().get('id')),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                if not category_id:
                                    category_obj.create({'magento_id':response.json().get('id'),'magento_instance_id':self.id,'position':response.json().get('position'),'level':response.json().get('Level'),
                                    'name':response.json().get('name'),'shop_id':shop.id,})
                            if len(response.json().get('children_data')):
                                sub_categ=response.json().get('children_data')
                                for categ in sub_categ:
                                    sub_categ_id=self.env['product.category'].search([('magento_id','=',categ['id']),('name','=',categ['name']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                    if not sub_categ_id:
                                        categ_id=self.env['product.category'].search([('magento_id','=',categ['parent_id']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                        if categ_id:
                                            self.env['product.category'].create({'parent_id':categ_id.id,'magento_id':categ['id'],'name':categ['name'],
                                            'magento_instance_id':self.id,'position':categ['position'],'level':categ['level'],'shop_id':shop.id,'category_exported':True})
                                    for sub_in_sub in categ['children_data']:
                                        sub_in_sub_cat_id = self.env['product.category'].search([('magento_id','=',sub_in_sub['id']),('name','=',sub_in_sub['name']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                        if not sub_in_sub_cat_id:
                                            cat_id=self.env['product.category'].search([('magento_id','=',sub_in_sub['parent_id']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                            if cat_id:
                                                self.env['product.category'].create({'parent_id':cat_id.id,'magento_id':sub_in_sub['id'],'name':sub_in_sub['name'],'magento_instance_id':self.id,
                                                'position':sub_in_sub['position'],'level':sub_in_sub['level'],'shop_id':shop.id,'category_exported':True})
                                        if sub_in_sub['children_data']:
                                            for sub_to_sub in sub_in_sub['children_data']:
                                                sub_to_sub_cat_id = self.env['product.category'].search([('magento_id','=',sub_to_sub['id']),('name','=',sub_to_sub['name']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                                if not sub_to_sub_cat_id:
                                                    catsub_id=self.env['product.category'].search([('magento_id','=',sub_to_sub['parent_id']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                                    if catsub_id:
                                                        self.env['product.category'].create({'parent_id':catsub_id.id,'magento_id':sub_to_sub['id'],'name':sub_to_sub['name'],'magento_instance_id':self.id,'position':sub_to_sub['position'],
                                                                                    'level':sub_to_sub['level'],'shop_id':shop.id,'category_exported':True})
                                                if sub_to_sub['children_data']:
                                                    for sub_cat in sub_to_sub['children_data']:
                                                        sub_child_id = self.env['product.category'].search([('magento_id','=',sub_cat['id']),('name','=',sub_cat['name']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                                        if not sub_child_id:
                                                            sub_child_ids=self.env['product.category'].search([('magento_id','=',sub_cat['parent_id']),('magento_instance_id','=',self.id),('shop_id','=',shop.id)])
                                                            if sub_child_ids:
                                                                self.env['product.category'].create({'parent_id':sub_child_ids.id,'magento_id':sub_cat['id'],'name':sub_cat['name'],'magento_instance_id':self.id,'position':sub_cat['position'],
                                                                                            'level':sub_cat['level'],'shop_id':shop.id,'category_exported':True})
                        self._cr.commit()
                    except Exception as exc:
                        logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
                        pass 
        except Exception as exc:
            logger.error('*=========>  EXCEPTION <=========  ::  %s', exc)
        return True

    def ExportMultipleMagentoCategories(self):
        category_obj = self.env['product.category']
        category_ids = category_obj.search([('magento_instance_id','=',self.id),('category_exported','=',False)])
        for category_id in category_ids:
            category_id.GtExportMagentoCategory()
        return True   
    
    def GtExportMagentoProducts(self):
        product_obj = self.env['product.product']
        product_ids = product_obj.search([('magento_instance_ids','=',self.id),('magento_product','=',True),('exported_magento','=',False)])
        for product_id in product_ids:
            product_id.GtExportMagentoProducts()
        
        return True
       
    def GtExportProductImage(self):
        return True
    
    def GtImportMagentoSimpleProduct(self):
        if not self.count_magento_shop:
            raise UserError(_('Please Create Store!'))
        if not self.count_magento_websites:
            raise UserError(_('Please Create Website!'))
        if not self.count_magento_attributes:
            raise UserError(_('Please Create Attributes!'))
        if not self.count_magento_categories:
            raise UserError(_('Please Create Categories!'))
        if not self.count_magento_products:
            raise UserError(_('Please Create Products!'))

        product_obj = self.env['product.product']
        store_obj = self.env['gt.magento.store']
        website_obj = self.env['gt.magento.website']
        self.generate_token()
        token=self.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }
        url=str(self.location)+"/rest/V1/products?searchCriteria[filterGroups][0][filters][0][field]=type_id& searchCriteria[filterGroups][0][filters][0][value]=simple& searchCriteria[filterGroups][0][filters][0][conditionType]=eq&searchCriteria[page_size]=0"
        response = requests.request("GET",url, headers=headers)
        product_list=json.loads(response.text)
        for products in product_list['items']:
            each_product = products
            if 'extension_attributes' in each_product:
                extenstion_attributes = each_product.get('extension_attributes')
                if 'website_ids' in extenstion_attributes:
                    website_ids = extenstion_attributes.get('website_ids')
#            for attributes in each_product.get('custom_attributes'):
#                if attributes.get('attribute_code') == 'website_ids':
                    for website in website_ids:
                        website_id = website_obj.search([('website_id','=',website),('magento_instance_id','=',self.id)])
                        store_ids = store_obj.search([('website_id','=',website_id.id),('magento_instance_id','=',self.id)])
                        for store_id in store_ids:
                            product_obj.create_simple_products(self,headers,products['sku'],store_id,website_id)
        if len(product_list['items']) == 0:
            self.write({'from_id':self.to_id})
        return True
    
    def GtImportMagentoConfigurableProduct(self):
        if not self.count_magento_shop:
            raise UserError(_('Please Create Store!'))
        if not self.count_magento_websites:
            raise UserError(_('Please Create Website!'))
        if not self.count_magento_attributes:
            raise UserError(_('Please Create Attributes!'))
        if not self.count_magento_categories:
            raise UserError(_('Please Create Categories!'))

        product_obj = self.env['product.product']
        store_obj = self.env['gt.magento.store']
        website_obj = self.env['gt.magento.website']

        if self.token:
            token = self.token
        else:
            token = self.generate_token()
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }

        url = str(self.location)+"/rest/V1/products?searchCriteria[filterGroups][0][filters][0][field]=type_id& searchCriteria[filterGroups][0][filters][0][value]=configurable& searchCriteria[filterGroups][0][filters][0][conditionType]=eq&searchCriteria[page_size]=0"
        response = requests.request("GET",url, headers=headers)
        product_list = json.loads(response.text)

        for products in product_list['items']:
            url=str(self.location)+"/rest/V1/products/"+str(products['sku']).encode('utf-8').decode()
            response = requests.request("GET",url, headers=headers, stream=True)
            each_product=json.loads(response.text)

            if 'extension_attributes' in each_product:
                extenstion_attributes = each_product.get('extension_attributes')
                if 'website_ids' in extenstion_attributes:
                    website_ids = extenstion_attributes.get('website_ids')

            for website_id in website_ids:
                website_id = website_obj.search([('website_id','=',website_id),('magento_instance_id','=',self.id)])
                store_ids = store_obj.search([('website_id','=',website_id.id),('magento_instance_id','=',self.id)])
                for store_id in store_ids:
                    product_obj.create_configurable_magento_products(self, headers, products['sku'], store_id,website_id)
                    self._cr.commit()

        if len(product_list['items']) == 0:
            self.write({'config_prod_from_id':self.config_prod_to_id})
        return True

    def GtImportMagentoProductSkuForce(self):
        product_obj = self.env['product.product']
        store_obj = self.env['gt.magento.store']
        if self.token:
            token = self.token
        else:
            token = self.generate_token()

        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }

        store_ids = store_obj.search([('magento_instance_id','=',self.id)])

        for store in store_ids:
            for sku_reference in self.sku_reference_ids:
                product_obj.create_configurable_magento_products(self, headers, sku_reference.name, store, store.website_id)

    def GtImportMagentoCustomer(self):
        self.generate_token()
        token=self.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {'authorization':auth_token}
        url=str(self.location)+"/rest/V1/customers/search?searchCriteria[page_size]=0"
        response = requests.request("GET",url, headers=headers)
        customer_list=response.json().get('items')
        for customer in customer_list:
            self.CreateMagentoCustomer(customer)
        return True
    
    def CreateMagentoCustomer(self, customer):
        partner_obj = self.env['res.partner']

        partner_vals = {
            'name' : str(customer['firstname']) + str(customer['lastname']),
            'email' : customer['email'],
            'mag_cust_id':customer['id'],
            'customer_rank' : True,
            'magento_instance_ids':self.id,
            'mag_website_in': customer['created_in'] if 'created_in' in customer else '',
            'magento_customer':True,
        }
        partner_id=partner_obj.search([('mag_cust_id','=',customer['id']),('magento_instance_ids','=',self.id)])
        if not partner_id:
            partner_id = partner_obj.create(partner_vals)
        else:
            partner_obj.write(partner_vals)
        if partner_id:
            self.createMagentoAddress(customer["addresses"],partner_id)
        return partner_id
    
    def createMagentoAddress(self, address,partner_id):
        for cust_address in address:
            partner_vals={}
            company = []
            address_type = ''
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
            if len(cust_address.get('street',False)):
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
            if cust_address.get('default_billing') == True:
                address_type = 'invoice'
            if cust_address.get('default_shipping') == True:
                address_type = 'delivery'
            partner_vals.update({
                'mag_address_id':cust_address.get(str('id')),
                'name':cust_address.get("firstname",False) + ' ' + cust_address.get("lastname",False),
                'phone':cust_address.get('telephone',False),
                'zip':cust_address.get('postcode',False),
                'city':cust_address.get('city',False),
                'magento_customer': True,
                'mag_cust_id':cust_address.get(str('customer_id')),
                'parent_id':partner_id.id,
                'type': address_type,
                          })
            child_id=self.env['res.partner'].search([('mag_address_id','=',cust_address.get(str('id'))),('mag_cust_id','=',cust_address.get(str('customer_id')))])
            if not child_id:
                child_id = self.env['res.partner'].create(partner_vals)
                self._cr.commit()
            else:
                child_id = self.env['res.partner'].write(partner_vals)
            
            if 'vat_id' in cust_address:
                partner_id.write({'vat': cust_address['vat_id']})

        return True
      
    def GtImportProductImage(self):
        if not self.count_magento_shop:
            raise UserError(_('Please Create Store!'))
        if not self.count_magento_websites:
            raise UserError(_('Please Create Website!'))
        if not self.count_magento_attributes:
            raise UserError(_('Please Create Attributes!'))
        if not self.count_magento_categories:
            raise UserError(_('Please Create Categories!'))
        if not self.count_magento_products:
            raise UserError(_('Please Create Products!'))

        count = 0
        pro_obj=self.env['product.template']
        shop_obj=self.env['gt.magento.store']
        shop_ids=shop_obj.search([])
        if not shop_ids:
            raise UserError(_('Please Create Store'))
        self.generate_token()
        headers = {
            'authorization':"Bearer "+self.token
            }
        product_ids = pro_obj.search([('active','=',True),('magento_id','!=','')])
        print("*==> Total of products:: ", len(product_ids))
        if product_ids: 
            for prod_data in product_ids:
                if prod_data.magento_sku:
                    url=self.location+"/rest/V1/products/"+str(prod_data.magento_sku)+"/media"
                    response = requests.request("GET",url, headers=headers)
                    if str(response.status_code)=='200':
                        count+=1
                        print("*==> product #",count)
                        list_prods=json.loads(response.text)
                        self.create_image(prod_data,list_prods)
        return True
    
    def create_image(self, prod_data, list_prods):
        img_obj=self.env['product.photo']
        multi_instance = self.env['gt.magento.product.image.multi']
        for list_prod in list_prods:
            if list_prod['id']:
                image_name=list_prod['file'].split('.')[0].split('/')[-1]
                url = self.location +  '/pub/media/catalog/product' + list_prod['file']
                file_contain = urllib.request.urlopen(url).read()
                image_path = base64.encodestring(file_contain)

                vals = {
                        'magento_url': list_prod['file'],
                        'name': image_name,
                        'link': 1,
                        'url': url,
                        'product_id': prod_data.id,
                        'is_exported': True,
                        'magento_id': list_prod['id']
                }
                if len(list_prod['types']):
                    for image_type in list_prod['types']:
                        if 'image' in image_type:
                            vals.update({'base_image':True})
                        if 'small_image' in image_type:
                            vals.update({'small_image':True})
                        if 'thumbnail' in image_type:
                            vals.update({'thumbnail':True})

                img_ids = img_obj.search([('name','=',image_name),('product_id','=',prod_data.id)])
                if img_ids:
                    instance_ids = []
                    if len(img_ids.magento_instance_ids) > 0:
                        for old_instance_id in self.magento_instance_ids:
                            instance_ids.append(old_instance_id.id)
                        vals.update({'magento_instance_ids':[(6,0,instance_ids)]})
                    image_id = img_ids.write(vals)
                    logger.error('write image=============:  %s', image_id)
                    logger.error('write image=============:  %s', image_id)
                else:
                    img_ids =img_obj.create(vals)
                    if img_ids and img_ids[0].link==True:
                        file_data = urllib.request.urlopen(img_ids.url).read()
                        image_path = base64.encodestring(file_data)
                        image_id = img_ids.write({'image':image_path})
                instance_id = multi_instance.search([('magento_id','=',list_prod['id']),('gt_magento_instance_id','=',self.id),('gt_magento_exported','=',True),('images_ids','=',img_ids.id)])
                if not instance_id:
                    instance_id = multi_instance.create({'magento_id':list_prod['id'],'gt_magento_instance_id':self.id,'gt_magento_exported':True,'images_ids':img_ids.id})
                prods_id = []
                for prod_id in img_ids.gt_magento_image_ids:
                    prods_id.append(prod_id.id)
                if instance_id.id not in prods_id:
                    prods_id.append(instance_id.id)
                img_ids.write({'gt_magento_image_ids':[(6,0,prods_id)]})
            image_data=img_obj.search([('product_id','=',prod_data.id)])
            if image_data and image_data[0].link== True:
                file_contain = urllib.request.urlopen(image_data[0].url).read()
                image_path = base64.encodestring(file_contain)
            else:
                image_path = image_data.image
            update=prod_data.write({'image_1920':image_path})
            print("*=> upload image...")
        self._cr.commit()
        return True

    def GtImportMagentoStock(self):
        try:
            product_obj=self.env['product.product']
            stock_inve_line_obj=self.env['stock.inventory.line']
            stock_inv_obj=self.env['stock.inventory']
            self.generate_token()
            headers = { 'authorization':"Bearer "+self.token}
            product_list = product_obj.search([('magento_instance_ids','=',self.id),('magento_product','=',True)])
            inventory_id = stock_inv_obj.create({'name':'update stock'+' '+str(datetime.datetime.now())})
            for product in product_list:
                try:
                    if product.default_code:
                        url=self.location+"/rest/V1/stockItems/"+str(product.default_code)+"?=0"
                        response = requests.request("GET",url, headers=headers)
                        each_response=json.loads(response.text)
                        if ('qty') in each_response:
                            if (each_response['qty']) != None:
                                if float(each_response['qty']) > 0.0000:
                                    data = stock_inve_line_obj.create({'inventory_id':inventory_id.id,'location_id':self.location_id.id,'product_id':product.id,'product_qty':each_response['qty']})
                                    self._cr.commit()
                except Exception as exc:
                        logger.error('*=========>  EXCEPTION <=========  :: %s', exc)
                        pass 

            inventory_id._action_done()
            self._cr.commit()
        except Exception as exc:
            logger.error('*=========>  EXCEPTION <=========  ::  %s', exc)
            pass
        return True
    
    def GtExportProductStock(self):
        multi_instance = self.env['gt.magento.product.multi']
        try:
            product_obj=self.env['product.product']
            (instances,)=self.browse(self._ids)
            instances.generate_token()
            headers = {
                'authorization':"Bearer "+instances.token,
                'content-type': "application/json",
                'cache-control': "no-cache",
                }
            product_list = product_obj.search([('magento_instance_ids','=',self.id),('magento_product','=',True)])
            for product in product_list:
                multi_id = multi_instance.search([('gt_magento_instance_id','=',self.id),('gt_magento_exported','=',True),('product_id','=',product.id)])
                try:
                    if product.qty_available > 0.00:
                        vals = { "stockItem": {
                            "itemId": 0,
                            "productId": multi_id.magento_id,
                            "stockId": 1,
                            "qty": product.qty_available,
                            "isInStock": "true",
                            "extensionAttributes": {}
                          }
                        }
                        payload = str(vals) 
                        payload=payload.replace("'",'"')     
                        payload=str(payload)
                        url=self.location+"/rest/V1/products/"+str(product.default_code)+"/stockItems/"+"0"
                        response = requests.request("PUT",url, data=payload, headers=headers)
                        if str(response.status_code)=="200":
                            each_response=json.loads(response.text)
                except Exception as exc:
                        logger.error('Exception===================:  %s', exc)
                        pass 
        except Exception as exc:
            logger.error('Exception===================:  %s', exc)
            pass
        return True

    def update_configurable_magento_product(self, sku, store_id, website_id):
        return True