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


import logging
logger = logging.getLogger('stock')
import pytz
from datetime import datetime
from odoo import api, fields, models, _
from xml.dom.minidom import parse, parseString
import xml.etree.ElementTree as ET
# from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.prestashop_connector_gt.prestapyt.prestapyt import PrestaShopWebServiceError as PrestaShopWebServiceError
from odoo.addons.prestashop_connector_gt.prestapyt.prestapyt import PrestaShopWebService as PrestaShopWebService
from odoo.addons.prestashop_connector_gt.prestapyt.prestapyt import PrestaShopWebServiceDict as PrestaShopWebServiceDict


    
class prestashop_instance(models.Model):
    _name = 'prestashop.instance'
    _description = 'Prestashop Instance'

    def _select_versions(self):
        """ Available versions
        Can be inherited to add custom versions.
        """
        return [('1.6', '1.6')]


    name = fields.Char('Name')
    version = fields.Selection(_select_versions,string='Version',required=True,default='1.6')
    location = fields.Char('Location',default='http://localhost/prestashop',required=True)
    webservice_key = fields.Char('Webservice key',help="You have to put it in 'username' of the PrestaShop ""Webservice api path invite",required=True)
    warehouse_id=fields.Many2one('stock.warehouse','Warehouse', help='Warehouse used to compute the stock quantities.')
    company_id= fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    shipping_product_id=fields.Many2one('product.product', 'Shipping Product')

#     Count Button For Sale Shop
    presta_id = fields.Char(string='shop Id')
    sale_shop_count = fields.Integer(string='Shops\s Count', compute='get_shop_count', default=0)

    # @api.multi
    @api.depends('presta_id')
    def get_shop_count(self):
        sale_shop_obj = self.env['sale.shop']
        res = {}
        for shop in self:
            multishop_ids = sale_shop_obj.search([('prestashop_instance_id', '=', shop.id)])
            shop.sale_shop_count = len(multishop_ids.ids)
            # print "yhihh====>",len(multishop_ids.ids)
        return res


    # @api.multi
    def action_get_sale_shop(self):
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
        }

        return result


    # @api.one
    def create_shop(self, shop_val):
        sale_shop_obj = self.env['sale.shop']
        price_list_obj = self.env['product.pricelist']
        journal_obj = self.env['account.journal']
        company_obj = self.env['res.company']
        warehouse_obj = self.env['stock.warehouse']
        product_temp_obj = self.env['product.template']
        product_prod_obj = self.env['product.product']
        presta_instance_obj = self.env['prestashop.instance']
        location_route_obj = self.env['stock.location.route']
        workflow_obj = self.env['import.order.workflow']
        res_partner_obj = self.env['res.partner']
        shop_obj = self.env['sale.shop']

        def_journal_ids = journal_obj.search([('type', '=', 'bank')])
        def_pricelist_ids = price_list_obj.search([])
#         def_route_ids = location_route_obj.search([('name','=',"Make To Order")])
        def_workflow_ids = workflow_obj.search([('name','=','Basic Workflow')])
        def_partner_ids = res_partner_obj.search([('name','=','Guest'),('company_type','=','person')])
        company_ids = company_obj.search([])
        def_ship_ids = product_prod_obj.search([('type', '=', 'service'),('name','like','%Shipping%')])
        def_gift_ids = product_prod_obj.search([('type', '=', 'service'), ('name', 'like', '%Gift%')])
        def_warehouse_ids = warehouse_obj.search([])

        shop_vals = {
            # 'name' : shop_val.get('name').get('value'),
            'name' : self.get_value_data(shop_val.get('name')),

            'prestashop_instance_id' : self.id,
            'prestashop_shop' : True,
            # 'presta_id': shop_val.get('id').get('value'),
            'presta_id': self.get_value_data(shop_val.get('id'))[0],

            'pricelist_id': def_pricelist_ids and def_pricelist_ids[0].id,
            'sale_journal': def_journal_ids and def_journal_ids[0].id,
            'company_id': company_ids and company_ids[0].id,
            'shipment_fee_product_id': def_ship_ids and def_ship_ids[0].id,
            'gift_wrapper_fee_product_id': def_gift_ids and def_gift_ids[0].id,
            'warehouse_id' : def_warehouse_ids and def_warehouse_ids[0].id,
            # 'prefix': shop_val.get('name').get('value'),
            'prefix': self.get_value_data(shop_val.get('name')),

#             'route_ids': [(6,0,[def_route_ids[0].id])],
            'partner_id' : def_partner_ids and def_partner_ids[0].id,
            'workflow_id': def_workflow_ids and def_workflow_ids[0].id,
        }
        # shop_ids = sale_shop_obj.search([('prestashop_instance_id', '=', self[0].id), ('name', '=', shop_val.get('name').get('value'))])
        shop_ids = sale_shop_obj.search([('prestashop_instance_id', '=', self[0].id),('name', '=',  self.get_value_data(shop_val.get('name'))[0])])

        if not shop_ids:
            sale_shop_id = sale_shop_obj.create(shop_vals)
#             sale_shop_id.import_product_attributes()
        else:
            sale_shop_id = shop_ids
        return sale_shop_id

    # @api.one
    def get_value_data(self, value):
      if isinstance(value, dict):
          return value.get('value')
      else:
          return value

                    
    # @api.multi
    def create_prestashop_shop_action(self):

        lang_obj = self.env['prestashop.language']
        sale_shop_obj = self.env['sale.shop']
        shop_ids = []
        for instance in self:
            prestashop = PrestaShopWebServiceDict(instance.location, instance.webservice_key)
            shops = prestashop.get('shops')
            # print "instance.shop_physical_url=====>",instance.shop_physical_url

            if shops.get('shops') and shops.get('shops').get('shop'):
                shops = shops.get('shops').get('shop')
                if isinstance(shops, list):
                    shops_val = shops
                else:
                    shops_val = [shops]

                for shop_id in shops_val:
                    id = shop_id.get('attrs').get('id')
                    data = prestashop.get('shops', id)
                    if data.get('shop'):
                        shop_id = sale_shop_obj.search([('presta_id','=',self.get_value_data(data.get('shop').get('id'))[0])])
                        if not shop_id:
                                shop_ids.append(instance.create_shop(data.get('shop')))
                
                languages = prestashop.get('languages')
                lan_vals = languages.get('languages').get('language')
                if isinstance(lan_vals, list):
                    lan_vals = languages.get('languages').get('language')
                else:
                    lan_vals = [languages.get('languages').get('language')]
                for lang in lan_vals:
                    logger.info('lang ===> %s', lang)
                    lang_vals = prestashop.get('languages', lang.get('attrs').get('id'))
                    logger.info('lang_vals===> %s', lang_vals)
                    # vals = {
                    #     'name': lang_vals.get('language').get('name').get('value'),
                    #     'code': lang_vals.get('language').get('iso_code').get('value'),
                    #     'presta_id' : lang_vals.get('language').get('id').get('value'),
                    #     'presta_instance_id' : instance.id
                    # }
                    vals = {
                        'name': self.get_value_data(lang_vals.get('language').get('name')),
                        'code': self.get_value_data(lang_vals.get('language').get('iso_code')),
                        'presta_id' : self.get_value_data(lang_vals.get('language').get('id')),
                        'presta_instance_id' : instance.id
                    }
                    # l_ids = lang_obj.search([('presta_id','=', lang_vals.get('language').get('id').get('value')),('presta_instance_id','=', instance.id)])
                    l_ids = lang_obj.search([('presta_id','=', self.get_value_data(lang_vals.get('language').get('id'))[0]),('presta_instance_id','=', instance.id)])
                    if not l_ids:
                        lang_obj.create(vals)
    #                 if shop_ids:
    #                     shop_ids.import_product_attributes()
        return True
