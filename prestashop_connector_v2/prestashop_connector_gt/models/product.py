# -*- coding: utf-8 -*-
#############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime, date, time
import time
from datetime import timedelta,datetime
import datetime
from odoo.tools.translate import _
import psycopg2
class product_template(models.Model):
    _inherit = 'product.template'
    
    prestashop_product_category = fields.Char('Prestashop Category',size=64)
    wholesale_price = fields.Float('Whole Sale Price',digits=(16,2))
    combination_price = fields.Float(string="Extra Price of combination")
    prdct_unit_price = fields.Float('Unit Price')
    prestashop_product = fields.Boolean('Prestashop Product')
    product_onsale = fields.Boolean('On sale')
    product_instock = fields.Boolean('In Stock')
    product_img_ids = fields.One2many('product.images','product_t_id','Product Images')
    prd_label = fields.Char('Label')
    supplier_id = fields.Many2one('res.partner','Supplier')
    manufacturer_id = fields.Many2one('res.partner','Manufacturer')
    product_lngth=fields.Float('Length')
    product_wght=fields.Float('Weight')
    product_hght=fields.Float('Height')
    product_width=fields.Float('Weight')
    prd_type_name=fields.Char('Product Type Name')
    prest_active=fields.Boolean('Active')
    prest_img_id=fields.Integer('Imge ID')
    product_list_id=fields.One2many('product.listing','product_id','Product Shops')
    presta_id = fields.Char('Presta ID')
    write_date = fields.Datetime(string="Write Date")
    tmpl_shop_ids = fields.Many2many('sale.shop', 'product_templ_shop_rel', 'product_id', 'shop_id', string="Shop")
    product_category_ids = fields.Many2many('product.category', 'product_template_categ_relation', 'product_id', 'categ_id', string="Category")
    product_shop_count = fields.Integer(string="Shops",compute = 'get_product_shop_count',default=0)
    product_to_be_exported = fields.Boolean(string="Product to be exported?")
    sku = fields.Char(string="SKU")

    # @api.multi
    def get_product_shop_count(self):
        for temp in self:
            temp.product_shop_count = len(temp.tmpl_shop_ids)



    # @api.multi
    def action_get_shop_product(self):
        action = self.env.ref('prestashop_connector_gt.act_prestashop_shop_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            # 'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': [('id', 'in', self.tmpl_shop_ids.ids)]
        }


        return result

product_template()






class product_product(models.Model):
    _inherit='product.product'

    prestashop_product=fields.Boolean('Prestashop Product')
    # shop_ids = fields.Many2many('sale.shop', 'product_prod_shop_rel', 'product_prod_id', 'shop_id', string="Shop")
    presta_id = fields.Char('Presta ID')

    combination_price = fields.Float(string="Extra Price of combination")
    combination_id = fields.Char(string="Combination ID")
    presta_inventory_id = fields.Char(string= 'Presta inventory ID')
    # v_product_img_ids = fields.One2many('product.images', 'product_v_id', 'Product Images')

    prodshop_ids = fields.Many2many('sale.shop', 'product_prod_shop_rel', 'product_prod_id', 'shop_id', string="Shop")
#     presta_id = fields.Char('Presta ID')

class product_images(models.Model):
    _inherit ='product.images'

    product_t_id=fields.Many2one('product.template','Product Images')
    image_url=fields.Char('Image URL')
    image=fields.Binary('Image')
    prest_img_id=fields.Integer('Img ID')
    is_default_img=fields.Boolean('Default')
    prest_product_id=fields.Integer('Presta Product ID')
    shop_ids = fields.Many2many('sale.shop', 'img_shop_rel', 'img_id', 'shop_id', string="Shop")
    write_date = fields.Datetime(string="Write Date")

class product_attribute(models.Model):
    _inherit='product.attribute'
    
    is_presta=fields.Boolean("Is Prestashop")
    public_name=fields.Boolean("Public Name")
    presta_id = fields.Char(string='Presta Id')
    shop_ids = fields.Many2many('sale.shop', 'attr_shop_rel', 'attr_id', 'shop_id', string="Shop")

class product_attribute_value(models.Model):
    _inherit= "product.attribute.value"

    _sql_constraints = [('value_company_uniq', 'CHECK(1=1)', 'You cannot create two values with the same name for the same attribute.')]

    is_presta=fields.Boolean("Is Prestashop")
    presta_id = fields.Char(string='Presta Id')
    write_date = fields.Datetime(string="Write Date")
    shop_ids = fields.Many2many('sale.shop', 'attr_val_shop_rel', 'attr_val_id', 'shop_id', string="Shop")


class product_category(models.Model):
    _inherit="product.category"
    presta_id =fields.Char("Presta ID")
    sequence = fields.Integer(  'Sequence', default=1, help="Assigns the priority to the list of product Category.")
    write_date = fields.Datetime(string="Write Date")
    is_presta = fields.Boolean("Is Prestashop")
    active = fields.Boolean("Active")
    friendly_url = fields.Char("Friendly URL")
    meta_title = fields.Char("Meta Title", size=70)
    meta_description = fields.Text("Meta description", )
    shop_id = fields.Many2one('sale.shop', 'Shop ID')
    shop_ids = fields.Many2many('sale.shop', 'categ_shop_rel', 'categ_id', 'shop_id', string="Shop")
    to_be_exported = fields.Boolean(string="To be exported?")

class product_listing(models.Model):
    _name='product.listing'
    shop_id=fields.Many2one('sale.shop','Shop ID')
    product_id =fields.Many2one('product.template','product_id')

class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'
    write_date = fields.Datetime(string="Write Date")
    presta_id = fields.Char("Presta ID")
    shop_ids = fields.Many2many('sale.shop', 'stockware_shop_rel', 'stockware_id', 'shop_id', string="Shop")

class stock_quant(models.Model):
    _inherit = 'stock.quant'

    presta_id = fields.Char("Presta ID")
    is_presta = fields.Char("Presta stock")


    
    @api.model
    def _get_inventory_fields_create(self):
        res = super(stock_quant, self)._get_inventory_fields_create()
        res.append('presta_id')
        res.append('is_presta')
        return res
