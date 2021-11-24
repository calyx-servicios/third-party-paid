from odoo import tools
from odoo import tools
from odoo import api, fields, models
from odoo.tools.translate import _
import io
import base64
from base64 import b64decode
#import pycurl
from StringIO import StringIO 
#import pycurl
import requests
from lxml import etree
import xml.etree.ElementTree as ET
# from urllib2 import Request, urlopen

class upload_products(models.TransientModel):
    _name="prestashop.upload.products"
    _description = 'Upload Products'
    
    prestashop_id=fields.Many2one('prestashop.instance','Prestashop Instance')    
    
    # @api.one
    def upload_products(self,res_ids=None,presta_id=None):
        if res_ids and isinstance(res_ids,list):
            rec_list=res_ids
            presta_inst_id=presta_id
        else:
            active_ids= self._context.get('active_ids')
            rec_list=active_ids
            presta_inst_id=self.prestashop_id.id
        for rec in rec_list:
            product_product_obj=self.env['product.product']
            prod_templ_obj=self.env['product.template']
            product_obj=prod_templ_obj.browse(rec)
            
            prestashop=self.env['sale.shop'].browse(presta_inst_id).presta_connect_json()
            prestashop.debug = True
            product_schema=prestashop.get('products',options={'schema': 'blank'})
            name_rewrite=product_obj.name
            x=name_rewrite.lower()
            new_name=x.replace(' ','-')
            if product_obj.default_code:
                ref=product_obj.default_code
                product_schema['product'].update({
                                             'reference': ref})
            product_schema['product'].update({
                                             'wholesale_price': str(product_obj.wholesale_price), 
#                                             'id_manufacturer':product_obj.manufacturer_products , 
                                             'weight': str(product_obj.product_wght), 
                                             'show_price': '1', 
                                             'on_sale': int(product_obj.product_onsale), 
                                             'width': str(product_obj.product_width), 
                                             'description_short': {'language': {'attrs': {'id': '1'}, 'value': product_obj.description}}, 
                                             'link_rewrite':{'language': {'attrs': {'id': '1'},'value':new_name}}, 
                                             'description': {'language': {'attrs': {'id': '1'}, 'value': product_obj.description}}, 
                                             'price': str(product_obj.list_price), 
                                             'height': str(product_obj.product_hght), 
                                             'name': {'language': {'attrs': {'id': '1'}, 'value': product_obj.name}}, 
                                             'depth': str(product_obj.product_lngth), 
                                             'active':int(product_obj.prest_active),
                                            })
#             if product_obj.barocde:
#                 product_schema['product'].update({'ean13':product_obj.barcode })
#               

                 
            if product_obj.product_instock:
                product_schema['product'].update({'available_for_order': '1'})
            else:
                product_schema['product'].update({'available_for_order': '0'})
            
            if product_obj.prestashop_category:
                categ_lis=product_obj.presta_categ_ids
                categ_id_list=self.upload_categories(prestashop,categ_lis)
                product_schema['product'].update({'id_category_default':categ_id_list[0]['id']}) 
                product_schema['product']['associations']['categories'].update({'category':categ_id_list})
                
            
            
            # create the product on prestashop            
            product_search_ids=prestashop.search('products',options={'filter[name]':product_obj.name})
                    
            if not product_search_ids:                                                                           #OR ELSE CREATE IT
                product_ids=prestashop.add('products',product_schema)
                id_product=product_ids['prestashop']['product']['id']                       #GET THE ID OF CREATED PRODUCT
    
            
                product_schema['product'].update({'id':id_product})
            else:
                id_product=product_search_ids[0]
            product_schema['product'].update({'id':id_product})
            img_list=[]
            try:
                x=prestashop.get('images/products/'+str(id_product))
                if x:
                    x_list= x['image']['declination']
                    if not isinstance(x_list,list):
                        x_list=[x_list]
                    for x_id in x_list:
                        img_list.append(x_id['attrs']['id'])
            except :
                pass
#             prestashop.edit('products',product_search_ids[0],product_schema)            
    
            prdct_search_ids=product_product_obj.search([('product_tmpl_id','=',rec)])   #CHECK IF THE PRODUCT HAS ANY VARIANTS
            if len(prdct_search_ids) > 1:
                product_comb_list=[]
                for prd_id in prdct_search_ids:
                    attr_value_ids=product_product_obj.browse(prd_id.id).attribute_value_ids
                    attr_id_list=[]
                    attr_value_list=[]
                    for attr_value_id in attr_value_ids:
                        attr_id_list.append(attr_value_id.attribute_id)
                        attr_value_list.append(attr_value_id.name)
                        
                    product_option_id=self.upload_product_options(prestashop,attr_id_list,attr_value_list)
                    
                    qty=product_product_obj.browse(prd_id.id).qty_available
                    ref=product_product_obj.browse(prd_id.id).default_code
                    price =product_product_obj.browse(prd_id.id).lst_price
                    product_comb_vals=self.upload_combinations(prestashop,id_product,qty,product_option_id,ref,price)     #iF VARIANTS, UPLOAD THE NAME AND QUNATITY OF THAT VARIANT
                    product_comb_list.append(product_comb_vals)
                    self.upload_inventory(prestashop,product_obj,id_product,prd_id.id,variant=True,product_comb_vals=product_comb_vals)  #UPDATE THE INVENTORY
                            
                product_schema['product']['associations']['combinations'].update({'combination':product_comb_list})     #ATTACH  THE COMBINATION TO PRODUCT
                product_schema['product'].update({'id_default_combination':product_comb_list[0]['id']})
            
            self.upload_inventory(prestashop,product_obj,id_product)   # To set the quantity of product we need to edit stock_availables.
            
            if product_obj.image_medium:
                for img_id in img_list:
                    data=base64.b64decode(product_obj.image_medium)
                    files={'image':data}
                    url=self.env['prestashop.instance'].browse(presta_inst_id).location
                    key=self.env['prestashop.instance'].browse(presta_inst_id).webservice_key
                    r=requests.delete(url+'/api/images/products/%s/%s'%(str(id_product),str(img_id)),files=files, auth=(key,''))
                    product_obj.write({'prest_img_id':False})
            
#                 if product_obj.product_img_ids:                                                 #CHECK IF THE PRODUCT HAS LIST OF IMAGES
#                     product_img_ids=product_obj.product_img_ids
#                     img_list=[]
#                     for img in product_img_ids:
#                         if img['image']:
#                             if img.prest_img_id:
#                                 data=base64.b64decode(product_obj.image_medium)
#                                 files={'image':data}
#                                 url=self.env['prestashop.instance'].browse(presta_inst_id).location
#                                 key=self.env['prestashop.instance'].browse(presta_inst_id).webservice_key
#                                 r=requests.delete(url+'/api/images/products/%s/%s'%(str(product_search_ids[0]),str(img.prest_img_id)),files=files, auth=(key,''))
#                                 img.write({'prest_img_id':False})
#                 
                prestashop.edit('products',product_search_ids[0],product_schema)                
                if product_obj.image_medium:                                                    # CHECK IF THE PRODUCT HAS AN IMAGE
                    image_vals=product_obj.image_medium
                    image_id=self.upload_images(presta_inst_id,id_product,image_vals)
                    if image_id:
                        product_obj.write({'prest_img_id':image_id})
                        product_schema['product'].update({'id_default_image':image_id })
                   
                self._cr.commit()            
                if product_obj.product_img_ids:                                                 #CHECK IF THE PRODUCT HAS LIST OF IMAGES
                    product_img_ids=product_obj.product_img_ids
                    img_list=[]
                    for img in product_img_ids:
                        if img['image']:
                            img_id=self.upload_images(presta_inst_id,id_product,img['image'])
                            img.write({'prest_img_id':img_id})
                            img_list.append({'id':img_id})
                            product_schema['product']['associations']['images'].update({'image': img_list})
                         
            
            elif product_search_ids and (not product_obj.image_medium or not product_obj.product_img_ids):          
                product_schema['product'].update({'id':id_product})
                prestashop.edit('products',product_search_ids[0],product_schema)
            
        return id_product
    
    def upload_inventory(self,prestashop,product_obj,id_product,product_obj_id=None,variant=False,product_comb_vals=None):
        prod_templ_obj=self.env['product.template']
        prdct_obj=self.env['product.product']
        inventry_line_obj=self.env['stock.inventory.line']
        
        if  variant != True:
            stock_avail_id=prestashop.search('stock_availables',options={'filter[id_product]':id_product})  #search the stock for this product
            tmpl_ids=prod_templ_obj.search([('default_code','=',product_obj.default_code)]) #To search the product qty in invemtory
            prd_ids=prdct_obj.search([('product_tmpl_id','=',tmpl_ids[0].id)])

            product_val=prdct_obj.browse(prd_ids[0].id)
    
            inv_id_unsorted=inventry_line_obj.search([('product_id','=',product_val.id)])
            inv_id=sorted(inv_id_unsorted,reverse=True)
            if inv_id:
                inventory_quantity=inventry_line_obj.browse(inv_id[0].id)
                stock_avail_schema=prestashop.get('stock_availables',options={'schema': 'blank'})   #get blank dictionary
                
                #update the stock_schema
                stock_avail_schema['stock_available'].update({
                                                             'id_product':id_product,   #product id
                                                             'id':stock_avail_id[0],        #stock_id imp
                                                             'id_product_attribute':'0',
                                                             'id_shop':'1',
                                                             'quantity':str(int(inventory_quantity.product_qty)),
                                                             'depends_on_stock':'0',
                                                             'out_of_stock':'0'
                
                                                           })
                #since stock avail is automatically created we just have to edit it.
                prestashop.edit('stock_availables',int(stock_avail_id[0]),stock_avail_schema)
        else:
            stock_avail_id=prestashop.search('stock_availables',options={'filter[id_product]':id_product,'filter[id_product_attribute]':product_comb_vals['id']})
            product_val=prdct_obj.browse(product_obj_id)
            inv_id_unsorted=inventry_line_obj.search([('product_id','=',product_val.id)])
            inv_id=sorted(inv_id_unsorted,reverse=True)
            if inv_id:
                inventory_quantity=inventry_line_obj.browse(inv_id[0].id)
                qty=str(int(inventory_quantity.product_qty))
            else:
                qty='0'
            
            stock_avail_schema=prestashop.get('stock_availables',options={'schema': 'blank'})   #get blank dictionary
            
            #update the stock_schema
            stock_avail_schema['stock_available'].update({
                                                         'id_product':id_product,   #product id
                                                         'id':stock_avail_id[0],        #stock_id imp
                                                         'id_product_attribute':product_comb_vals['id'],
                                                         'id_shop':'1',
                                                         'quantity':qty,
                                                         'depends_on_stock':'0',
                                                         'out_of_stock':'0'
            
                                                       })
            #since stock avail is automatically created we just have to edit it.
            prestashop.edit('stock_availables',int(stock_avail_id[0]),stock_avail_schema)
            
            
  
    # @api.multi
    def upload_categories(self,prestashop,category_list):
        categ_list=[]
        for category_obj in category_list:
            active=str(int(category_obj.presta_active))
            if category_obj.presta_active:
                category_name=category_obj.name
                code=category_obj.code
                is_root=str(int(category_obj.is_root))
                descript=category_obj.description
                category_schema=prestashop.get('categories',options={'schema':'blank'})
                category_schema['category'].update({
                                        'link_rewrite': {'language': {'attrs': {'id': '1'}, 'value': code}}, 
                                        'name': {'language': {'attrs': {'id': '1'}, 'value': category_name}}, 
                                        'id_shop_default': '1',   #Shop ID is set to 1
                                        'active': active,  
                                        'visible':'1',
                                        'id_parent': category_obj.id_parent,
                                        'is_root_category':is_root,
                                        'description': {'language': {'attrs': {'id': '1'}, 'value': descript}}})
                
                category_search_ids = prestashop.search('categories',options={'filter[name]':category_name})
                category_schema['category'].update({'id': category_obj.presta_shop_id})
                categ_list.append({'id': category_obj.presta_shop_id})
                prestashop.edit('categories', category_obj.presta_shop_id,category_schema)
#                     categ_list.append({'id':category_search_ids[0]})
#                 if category_search_ids:
#                     category_schema['category'].update({'id':category_search_ids[0]})
#                     prestashop.edit('categories',category_search_ids[0],category_schema)
#                     categ_list.append({'id':category_search_ids[0]})
#                 else:
#                     category = prestashop.add('categories',category_schema)  
#                     categ_id =  category['prestashop']['category']['id']
#                     categ_list.append({'id':category_obj.presta_shop_id})

        return categ_list
    
    def upload_product_options(self,prestashop,attr_id_list,attr_val_list):
        attribute_vals=[]
        for atrr_id in attr_id_list:
            attr_name=atrr_id.name
            attr_id=atrr_id.id
            product_optn_search_ids=prestashop.search('product_options',options={'filter[name]':attr_name})
            
            if not product_optn_search_ids:
                product_option_schema=prestashop.get('product_options',options={'schema':'blank'})
                product_option_schema['product_option'].update({'public_name': {'language': {'attrs': {'id': '1'}, 'value': attr_name}}, 
                                                                 'name': {'language': {'attrs': {'id': '1'}, 'value': attr_name}},
                                                                 'position': '0', 
                                                                 'is_color_group': '0', 
                                                                 'group_type': 'select'})
                product_optin=prestashop.add('product_options',product_option_schema) 
                product_option_id= product_optin['prestashop']['product_option']['id']
            else:
                product_option_id=product_optn_search_ids[0]
            if attr_val_list:
                for vals in attr_val_list:
                    vals_id=self.env['product.attribute.value'].search([('name','=',vals),('attribute_id','=',attr_id)])
                    if vals_id:
                        atr_val_id=self.upload_product_option_value(prestashop,product_option_id,vals)
                        attribute_vals.append(atr_val_id)
        return attribute_vals
    
    def upload_product_option_value(self,prestashop,product_option_id,vals):
        product_vals_search_ids=prestashop.search('product_option_values',options={'filter[name]':vals})
        if not product_vals_search_ids:
            product_vals_schema=prestashop.get('product_option_values',options={'schema':'blank'})
            product_vals_schema['product_option_value'].update({'id_attribute_group': product_option_id, 
                                                                'name': {'language': {'attrs': {'id': '1'}, 'value': vals}}, 
                                                                })
            product_vals_optn=prestashop.add('product_option_values',product_vals_schema)
            product_vals_id=product_vals_optn['prestashop']['product_option_value']['id']
        else:
            product_vals_id=product_vals_search_ids[0]    
        return  product_vals_id
 
    def upload_combinations(self,prestashop,product_id,quanty,product_vals_ids,ref,price):
        vals={}
        if ref:
            product_comb_search_ids=prestashop.search('combinations', options= {'filter[reference]':str(ref)})
        else:
            product_comb_search_ids=False
        if not product_comb_search_ids:
            product_comb_schema=prestashop.get('combinations',options={'schema':'blank'})
            product_comb_schema['combination'].update({
                                                           'id_product':product_id,
                                                           'quantity':str(int(quanty)),
                                                           'reference':ref,
                                                           'minimal_quantity':'1',
                                                           'price':price,
                                                           })
            product_vals_list=[]
            for val_id in product_vals_ids:
                product_vals_list.append({'id':val_id})
                
            product_comb_schema['combination']['associations']['product_option_values'].update({'product_option_value':product_vals_list})
            combination_elem=prestashop.add('combinations',product_comb_schema)
            comination_id=combination_elem['prestashop']['combination']['id']
            vals.update({'id':comination_id})
        else:
            vals.update({'id':product_comb_search_ids[0]}) 
        return vals
    
    def upload_images(self,presta_inst_id,id_product,image_data):
        pesta_obj=self.env['prestashop.instance'].browse(presta_inst_id)
        url=pesta_obj.location
        key=pesta_obj.webservice_key
        data=base64.b64decode(image_data)
#         image_id  = False
        files={'image': data}
        r = requests.post(url+'/api/images/products/'+str(id_product), files=files, auth=(key,''), allow_redirects=True)
        res = etree.fromstring(r.content)
        xpath_res = res.xpath('/prestashop/image')
        for element in xpath_res:
            for item in element.iter():
                if item.tag == 'id':
                        image_id=item.text
            
        return image_id
    
