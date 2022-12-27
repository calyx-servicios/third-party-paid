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

from odoo import fields,models,api,tools,_, SUPERUSER_ID
import requests
import json
import itertools
import psycopg2

import logging

from odoo.exceptions import ValidationError, RedirectWarning, UserError

_logger = logging.getLogger(__name__)
class ProductTemplate(models.Model):
    _inherit='product.template'
    
    magento_sku = fields.Char('Magento SKU')
    magento_id = fields.Char(string='Magento ID')
    magento_template = fields.Boolean(string='Magento Template')
    magento_exported = fields.Boolean(string='Template Magento Exported')
    magento_instance_ids = fields.Many2many('gt.magento.instance','mage_temp_rel','instas_id','templt_id','Magento Instance')
    prod_category_id = fields.Many2many('product.category', string='Magento Categories')
    prod_attr_category_id = fields.Many2one('gt.product.attribute.options', string='Magento Category')
    prod_images = fields.One2many('product.photo', 'product_id', 'Magento Images')

    def _create_variant_ids(self):
        self.flush()
        Product = self.env["product.product"]

        variants_to_create = []
        variants_to_activate = Product
        variants_to_unlink = Product

        for tmpl_id in self:
            lines_without_no_variants = tmpl_id.valid_product_template_attribute_line_ids._without_no_variant_attributes()

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted('active')

            current_variants_to_create = []
            current_variants_to_activate = Product

            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            single_value_lines = lines_without_no_variants.filtered(lambda ptal: len(ptal.product_template_value_ids._only_active()) == 1)
            if single_value_lines:
                for variant in all_variants:
                    combination = variant.product_template_attribute_value_ids | single_value_lines.product_template_value_ids._only_active()
                    # Do not add single value if the resulting combination would
                    # be invalid anyway.
                    if (
                        len(combination) == len(lines_without_no_variants) and
                        combination.attribute_line_id == lines_without_no_variants
                    ):
                        variant.product_template_attribute_value_ids = combination

            # Determine which product variants need to be created based on the attribute
            # configuration. If any attribute is set to generate variants dynamically, skip the
            # process.
            # Technical note: if there is no attribute, a variant is still created because
            # 'not any([])' and 'set([]) not in set([])' are True.
            if not tmpl_id.has_dynamic_attributes():
                # Iterator containing all possible `product.template.attribute.value` combination
                # The iterator is used to avoid MemoryError in case of a huge number of combination.
                all_combinations = itertools.product(*[
                    ptal.product_template_value_ids._only_active() for ptal in lines_without_no_variants
                ])
                # Set containing existing `product.template.attribute.value` combination
                existing_variants = {
                    variant.product_template_attribute_value_ids: variant for variant in all_variants
                }
                # For each possible variant, create if it doesn't exist yet.
                for combination_tuple in all_combinations:
                    combination = self.env['product.template.attribute.value'].concat(*combination_tuple)
                    if combination in existing_variants:
                        current_variants_to_activate += existing_variants[combination]
                    else:
                        current_variants_to_create.append({
                            'product_tmpl_id': tmpl_id.id,
                            'product_template_attribute_value_ids': [(6, 0, combination.ids)],
                            'active': tmpl_id.active,
                            'magento_id': tmpl_id.magento_id,
                            'magento_product':tmpl_id.magento_template,
                        })
                        if len(current_variants_to_create) > 1000:
                            raise UserError(_(
                                'The number of variants to generate is too high. '
                                'You should either not generate variants for each combination or generate them on demand from the sales order. '
                                'To do so, open the form view of attributes and change the mode of *Create Variants*.'))
                variants_to_create += current_variants_to_create
                variants_to_activate += current_variants_to_activate

            variants_to_unlink += all_variants - current_variants_to_activate
        if variants_to_activate:
            variants_to_activate.write({'active': True})
        if variants_to_create:
            Product.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink._unlink_or_archive()

        # prefetched o2m have to be reloaded (because of active_test)
        # (eg. product.template: product_variant_ids)
        # We can't rely on existing invalidate_cache because of the savepoint
        # in _unlink_or_archive.
        self.invalidate_cache()
        return True

    def GtUpdateMagentoProductTemplate(self):
        for rec in self:
            instance = rec.magento_instance_ids
            if rec.magento_exported and rec.magento_id and rec.magento_sku and instance: 
                
                product_obj = self.env['product.product']
                store_obj = self.env['gt.magento.store']
                website_obj = self.env['gt.magento.website']
                prod_cat_obj = self.env['product.category']
                prod_att_option_obj = self.env['gt.product.attribute.options']
                prod_att_obj = self.env['product.attribute']
                attribute_obj =self.env['gt.product.attributes']


                if instance[0].token:
                    token = instance[0].token
                else:
                    token = instance[0].generate_token()
                
                token=token.replace('"'," ")
                auth_token = "Bearer "+token.strip()
                auth_token = auth_token.replace("'",'"')
                headers = {
                    'authorization':auth_token,
                    'content-type': "application/json",
                    'cache-control': "no-cache",
                    }
                filter_product_type = "searchCriteria[filterGroups][0][filters][0][field]=type_id& searchCriteria[filterGroups][0][filters][0][value]=configurable& searchCriteria[filterGroups][0][filters][0][conditionType]=eq"
                filter_sku = "searchCriteria[filterGroups][0][filters][0][field]=sku&searchCriteria[filterGroups][0][filters][0][value]=%s& searchCriteria[filterGroups][0][filters][0][conditionType]=eq" % self.magento_sku

                url = str(instance[0].location) + ("/rest/V1/products?%s&%s") % (filter_product_type, filter_sku)
                response = requests.request("GET",url, headers=headers)
                product_list = json.loads(response.text)

                for products in product_list['items']:
                    url=str(instance[0].location)+"/rest/V1/products/"+str(products['sku']).encode('utf-8').decode()
                    response = requests.request("GET",url, headers=headers, stream=True)
                    each_product=json.loads(response.text)

                    if 'extension_attributes' in each_product:
                        extenstion_attributes = each_product.get('extension_attributes')
                        if 'website_ids' in extenstion_attributes:
                            website_ids = extenstion_attributes.get('website_ids')
                        if 'configurable_product_options' in extenstion_attributes:
                            prod_attributes = extenstion_attributes.get('configurable_product_options')

                    if 'custom_attributes' in each_product:
                        custom_atributes = each_product.get('custom_attributes')

                    prod_template_update_dict = {}
                    prod_website_ids = []
                    prod_store_ids = []
                    prod_categ_ids = []
                    prod_categ_id = False
                    attributes = []
                    attributes_update = []

                    for website_id in website_ids:
                        website_id = website_obj.search([('website_id','=',website_id),('magento_instance_id','=',instance[0].id)])
                        store_id = store_obj.search([('website_id','=',website_id.id),('magento_instance_id','=',instance[0].id)])
                        if website_id:
                            prod_website_ids.append(website_id.id)
                        if store_id:
                            prod_store_ids.append(store_id.id)

                    if each_product.get('name'):
                        prod_template_update_dict['name'] = each_product.get('name')
                    if each_product.get('price'):
                        prod_template_update_dict['list_price'] = each_product.get('price')

                    for attributes_child in custom_atributes:
                        if attributes_child['attribute_code'] == 'category_ids':
                            categ_id = attributes_child['value']
                            for each_category in categ_id:
                                categ_ids = prod_cat_obj.search([
                                    ('magento_id','=',each_category)
                                ])
                                if categ_ids:
                                    prod_categ_ids.append(categ_ids.id)
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
                            if categ_att_option_id:
                                prod_categ_id = categ_att_option_id
            
                    # import wdb
                    # wdb.set_trace()    
                    if prod_categ_ids:
                        prod_template_update_dict['prod_category_id'] = [(6, 0, prod_categ_ids)]
                    
                    if prod_categ_id:
                        prod_template_update_dict['prod_attr_category_id'] = prod_categ_id.id

                    for prod_attribute in prod_attributes:
                        attribute_mag_ids = attribute_obj.search([
                            ('magento_id','=',prod_attribute.get('attribute_id')),
                            ('referential_id','=',instance.id)
                        ])
                        if attribute_mag_ids:
                            attribute_ids = prod_att_obj.search([
                                ('attribute_magento_id','=',prod_attribute.get('attribute_id')),
                                ('is_attribute_magento','=',True)
                            ])
                            attrs_value_ids = []
                            
                            if attribute_ids: # atribute odoo
                                attribute = attribute_ids[0]
                                prod_attrs_value = rec.attribute_line_ids.filtered(lambda x: x.attribute_id == attribute)
                                prod_attrs_value_ids = prod_attrs_value.value_ids
                            else:
                                new_vals={
                                    'name':prod_attribute.get('label'),
                                    'create_variant':'always'
                                    }
                                attribute = prod_att_obj.create(new_vals)
                                print("*==> create odoo atribute! ::",new_vals)
                            
                            if not list(filter(lambda item: item['attribute'] == attribute.id, attributes)):
                                attribute_dict = {
                                    'attribute': attribute.id,
                                    'values': [],
                                }
                                attribute_dict_update = {
                                    'attribute': attribute.id,
                                    'values': [],
                                }
                                variant_list_attr = []
                                variant_list_attr_update = []

                                for values in prod_attribute.get('values'):
                                    prod_opt_ids = prod_att_option_obj.search([
                                        ('value', '=', values['value_index'])
                                    ]).filtered(lambda x: x.attribute_id.odoo_attr_id == attribute)
                                    if prod_attrs_value_ids:
                                        if prod_opt_ids[0].product_attr_value not in prod_attrs_value_ids:
                                            variant_list_attr_update.append(prod_opt_ids[0].product_attr_value.id)
                                    elif prod_opt_ids:
                                        if prod_opt_ids[0].product_attr_value.id not in variant_list_attr:
                                            variant_list_attr.append(prod_opt_ids[0].product_attr_value.id)
                                    else:
                                        print ("*==> THE PRODUCT DOES NOT HAVE OPTIONAL VALUES, IT MAY NOT HAVE BEEN IMPORTED: %s" % values['value_index']),
                                
                                attribute_dict['values'] = variant_list_attr
                                attribute_dict_update['values'] = variant_list_attr_update
                                if variant_list_attr:
                                    attributes.append(attribute_dict)
                                if variant_list_attr_update:
                                    attributes_update.append(attribute_dict_update)                        

                    if attributes:
                        variant_list = []
                        for att_line in attributes:
                            variant_list
                            variant_list.append((0,0,{
                                'attribute_id': att_line.get('attribute'),
                                'value_ids':[(6, 0, att_line.get('values'))]
                            }))
                        rec.attribute_line_ids = variant_list

                    if attributes_update:
                        variant_list = []
                        for att_line in attributes_update:
                            for value in att_line.get('values'):
                                variant_list.append((4, value, 0))
                        prod_tmpl_attr = rec.attribute_line_ids.filtered(lambda x: x.attribute_id.id == att_line['attribute'])
                        prod_tmpl_attr.write({'value_ids': variant_list})

                    self._cr.commit()
                    url = instance.location+"/rest/V1/configurable-products/"+str(rec.magento_sku).encode('utf-8').decode()+"/children" 
                    response = requests.request("GET",url, headers=headers)
                    child_product_list=json.loads(response.text)
                    
                    for child_product in child_product_list:           
                        value_id_list = []
                        for attr_id in rec.attribute_line_ids.mapped('attribute_id'):
                            attribute_magento = attribute_obj.search([
                                ('odoo_attr_id', '=', attr_id.id)
                            ])# atribute magento
                            for child in child_product.get('custom_attributes'):
                                if child.get('attribute_code') == attribute_magento.attribute_code:
                                    value_id = prod_att_option_obj.search([
                                        ('value','=',child.get('value')),
                                        ('attribute_id', '=', attribute_magento.attribute_code)
                                    ])# value of atribute magento
                                    if value_id:
                                        value_id_list.append(value_id.product_attr_value.id)
                        product_product = rec.product_variant_ids
                        
                        # import wdb
                        # wdb.set_trace()
                        
                        if product_product:
                            for product_ids in product_product:
                                attribute_list = []
                                for att_idss in product_ids.product_template_attribute_value_ids:
                                    attribute_list.append(att_idss.product_attribute_value_id.id)
                                if sorted(attribute_list, key=int) == sorted(value_id_list, key=int):
                                    product_ids.update_variant(child_product['sku'],instance,product_ids,headers,store_id,website_id)
                            self._cr.commit()

                    rec.write(prod_template_update_dict)

                if len(product_list['items']) == 0:
                    raise UserError('El SKU no existe en Magento')
                return True

    def GtUpdateProductImage(self):
        for rec in self:
            rec.prod_images.unlink()
            instance = rec.magento_instance_ids
            if rec.magento_exported and rec.magento_id and rec.magento_sku and instance: 
                
                if instance[0].token:
                    token = instance[0].token
                else:
                    token = instance[0].generate_token()
                
                token = token.replace('"'," ")
                auth_token = "Bearer "+token.strip()
                auth_token = auth_token.replace("'",'"')
                headers = {
                    'authorization':auth_token,
                    'content-type': "application/json",
                    'cache-control': "no-cache",
                    }

                url = instance.location+"/rest/V1/products/"+str(rec.magento_sku)+"/media"
                response = requests.request("GET",url, headers=headers)
                if str(response.status_code) == '200':
                    list_prods=json.loads(response.text)
                    instance.create_image(rec,list_prods)