# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, osv, models, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
import pdb
from .warning import warning
import requests
import operator as py_operator
from odoo.exceptions import UserError, ValidationError


from . import versions
from .versions import *

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}

class ProductecaConnectionBinding(models.Model):

    _name = "producteca.binding"
    _description = "Producteca Connection Binding"
    _inherit = "ocapi.connection.binding"

    #Connection reference defining mkt place credentials
    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )


class ProductecaConnectionBindingProductTemplate(models.Model):

    _name = "producteca.binding.product_template"
    _description = "Producteca Product Binding Product Template"
    _inherit = "ocapi.connection.binding.product_template"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )
    variant_bindings = fields.One2many( 'producteca.binding.product','binding_product_tmpl_id',string='Variant Bindings')

    def get_price_str_tmpl(self):
        prices = []
        prices_str = ""

        product_tpl = self.product_tmpl_id
        account = self.connection_account
        if not product_tpl or not account:
            return prices_str, [0]

        #self.with_context(pricelist=pricelist.id).price
        #for plitem in product.item_ids:
        for pl in account.configuration.publish_price_lists:
            plprice = product_tpl.with_context(pricelist=pl.id).price
            price = {
                "priceListId": pl.id,
                "priceList": pl.name,
                "amount": plprice,
                "currency": pl.currency_id.name
            }
            #prices.append(price)
            prices_str+= str(price["priceList"])+str(": ")+str(price["amount"])
            prices.append(plprice)

        if not prices:
            prices.append(0.0)

        return prices_str, prices

    def _calculate_price_resume_tmpl(self):
        #_logger.info("Calculate price resume")
        for bindT in self:
            #var.stock_resume = "LOEC: 5, MFULL: 3"
            price_resume_tmpl, prices = bindT.get_price_str_tmpl()
            bindT.price_resume_tmpl = price_resume_tmpl
            bindT.price = prices[0]


    def get_stock_str_tmpl(self):
        stocks = []
        stocks_str = ""
        #ss = variant._product_available()

        product_tmpl = self.product_tmpl_id
        account = self.connection_account
        if not product_tmpl or not account:
            return stocks_str

        #_logger.info("account.configuration.publish_stock_locations")
        #_logger.info(account.configuration.publish_stock_locations.mapped("id"))
        locids = account.configuration.publish_stock_locations.mapped("id")
        sq = self.env["stock.quant"].search([('product_tmpl_id','=',product_tmpl.id),('location_id','in',locids)],order="location_id asc")
        if (sq):
            #_logger.info( sq )
            #_logger.info( sq.name )
            for s in sq:
                #TODO: filtrar por configuration.locations
                #TODO: merge de stocks
                #TODO: solo publicar available
                if ( s.location_id.usage == "internal"):
                    _logger.info( s )
                    sjson = {
                        "warehouseId": s.location_id.id,
                        "warehouse": s.location_id.display_name,
                        "quantity": s.quantity,
                        "reserved": s.reserved_quantity,
                        "available": s.quantity - s.reserved_quantity
                    }
                    #stocks.append(sjson)
                    stocks_str+= str(sjson["warehouse"])+str(": ")+str(sjson["quantity"])+str("/")+str(str(sjson["available"]))
                    stocks_str+= " "
        return stocks_str

    def _calculate_stock_resume_tmpl(self):
        #_logger.info("Calculate stock resume")
        for bindT in self:
            bindT.stock_resume_tmpl = "LOEC: 5, MFULL: 3"
            bindT.stock_resume_tmpl = bindT.get_stock_str_tmpl()


    stock_resume_tmpl = fields.Char(string="Stock Resumen Tmpl", compute="_calculate_stock_resume_tmpl", store=False )
    price_resume_tmpl = fields.Char(string="Price Resumen Tmpl", compute="_calculate_price_resume_tmpl", store=False )
    #product_tmpl_company = fields.Many2one(related="product_tmpl_id.company_id",string="Company",store=True,index=True)
    product_tmpl_company = fields.Many2one(related="connection_account.company_id",string="Company (Account)",store=False,index=True)


class ProductecaConnectionBindingProductVariant(models.Model):

    _name = "producteca.binding.product"
    _description = "Producteca Product Binding Product"
    _inherit = ["producteca.binding.product_template","ocapi.connection.binding.product"]

    binding_product_tmpl_id = fields.Many2one("producteca.binding.product_template",string="Product Template Binding")

    def get_price_str(self):
        prices = []
        prices_str = ""

        variant = self.product_id
        account = self.connection_account
        if not variant or not account:
            return prices_str, [0]

        #self.with_context(pricelist=pricelist.id).price
        #for plitem in product.item_ids:
        for pl in account.configuration.publish_price_lists:
            plprice = variant.with_context(pricelist=pl.id).price
            price = {
                "priceListId": pl.id,
                "priceList": pl.name,
                "amount": plprice,
                "currency": pl.currency_id.name
            }
            #prices.append(price)
            prices_str+= str(price["priceList"])+str(": ")+str(price["amount"])
            self.price = plprice
            prices.append(plprice)

        if not prices:
            prices.append(0.0)

        return prices_str, prices

    def _calculate_price_resume(self):
        #_logger.info("Calculate price resume")
        for var in self:
            #var.stock_resume = "LOEC: 5, MFULL: 3"
            price_resume, prices = var.get_price_str()
            var.price_resume = price_resume
            var.price = prices[0]

    def get_stock_str(self):
        stocks = []
        stocks_str = ""
        stocks_on_hand = 0.0
        stocks_available = 0.0
        #ss = variant._product_available()

        variant = self.product_id
        account = self.connection_account
        if not variant or not account:
            return stocks_str, stocks_on_hand, stocks_available

        #_logger.info("account.configuration.publish_stock_locations")
        #_logger.info(account.configuration.publish_stock_locations.mapped("id"))
        locids = account.configuration.publish_stock_locations.mapped("id")
        sq = self.env["stock.quant"].search([('product_id','=',variant.id),('location_id','in',locids)],order="location_id asc")
        if (sq):
            #_logger.info( sq )
            #_logger.info( sq.name )
            for s in sq:
                #TODO: filtrar por configuration.locations
                #TODO: merge de stocks
                #TODO: solo publicar available
                if ( s.location_id.usage == "internal"):
                    _logger.info( s )
                    sjson = {
                        "warehouseId": s.location_id.id,
                        "warehouse": s.location_id.display_name,
                        "quantity": s.quantity,
                        "reserved": s.reserved_quantity,
                        "available": s.quantity - s.reserved_quantity
                    }
                    #stocks.append(sjson)
                    stocks_str+= str(sjson["warehouse"])+str(": ")+str(sjson["quantity"])+str("/")+str(str(sjson["available"]))
                    stocks_str+= " "
                    stocks_on_hand+= sjson["quantity"]
                    stocks_available+= sjson["available"]
                    #variant.stock = sjson["available"]

        return stocks_str, stocks_on_hand, stocks_available

    def _calculate_stock_resume(self):
        #_logger.info("Calculate stock resume")
        for var in self:
            var.stock_resume = ""
            stocks_str, stocks_on_hand, stocks_available = var.get_stock_str()
            var.stock_resume = stocks_str
            var.stock_resume_on_hand = stocks_on_hand
            var.stock_resume_available = stocks_available

    def _calculate_code_resume( self ):
        for var in self:
            var.code_resume = (var.product_id and var.product_id.barcode) or ""
            var.barcode = (var.product_id and var.product_id.barcode) or ""
            var.sku = (var.product_id and var.product_id.default_code) or ""

    stock_resume = fields.Char(string="Stock Resumen", compute="_calculate_stock_resume", store=False )
    price_resume = fields.Char(string="Price Resumen", compute="_calculate_price_resume", store=False )
    code_resume = fields.Char(string="Codes",compute="_calculate_code_resume", store=False)

    price = fields.Float(string="Price", compute="_calculate_price_resume", store=False)


    def _search_stock_resume_on_hand(self, operator, value):
        ids = []
        if (operator == '>' or operator == '<' or operator == '=' or operator == '>=' or operator == '<='):

            company = self.env.user.company_id
            account = company.producteca_connections and company.producteca_connections[0]
            if not account:
                return []

            locids = account.configuration.publish_stock_locations.mapped("id")
            sq = self.env["stock.quant"].search([('location_id','in',locids),('quantity',operator,value)],order="quantity asc")
            if sq:
                pids = sq.mapped("product_id")
                vbids = self.search([('product_id','in', pids.ids)])
                if vbids:
                    ids = [('id','in',vbids.ids)]

        return ids

    def _search_stock_resume_available(self, operator, value):
        ids = []
        if (operator == '>' or operator == '<' or operator == '=' or operator == '>=' or operator == '<='):

            company = self.env.user.company_id
            account = company.producteca_connections and company.producteca_connections[0]

            if not account:
                return []
            locids = account.configuration.publish_stock_locations.mapped("id")

            rsq = self.env["stock.quant"].search([('location_id','in',locids),('reserved_quantity','>',0.0)],order="reserved_quantity asc")
            sq = self.env["stock.quant"].search([('location_id','in',locids),('quantity',operator,value)],order="quantity asc")

            pids = []

            if sq:
                products_quantity = sq.mapped("product_id")
                pids = products_quantity

            if rsq:
                products_reserved = rsq.mapped("product_id")
                pids_reserved = products_reserved.ids
                products_not_reserved = products_quantity - products_reserved
                for q in rsq:
                    qav = q.quantity - q.reserved_quantity
                    if OPERATORS[operator](qav, value):
                        products_not_reserved+= q.product_id
                pids = products_not_reserved

            if pids:
                #_logger.info(pids.ids)
                vbids = self.search([('product_id','in', pids.ids)])
                #_logger.info(vbids)
                if vbids:
                    ids = [('id','in',vbids.ids)]

        return ids

    stock_resume_on_hand = fields.Float(string="Qty On hand", compute="_calculate_stock_resume"
                        , search="_search_stock_resume_on_hand"
                        )
    stock_resume_available = fields.Float(string="Qty Available", compute="_calculate_stock_resume"
                        , search="_search_stock_resume_available"
                        )

    def _product_main_cat( self ):
        for b in self:
            b.product_main_cat = None
            b.product_main_cat_child = None
            p = b.product_id
            if p:
                child = (p.categ_id and p.categ_id.parent_id)
                main = (child and child.parent_id)
                if not main:
                    child = p.categ_id
                #down_one = (child.parent_id == False) and
                #child_is = p.categ_id and p.categ_id.parent_id
                b.product_main_cat_child = child
                b.product_main_cat = child and child.parent_id

    def _product_size_color( self ):
        for b in self:
            b.product_size = None
            b.product_color = None
            b.product_gender = None
            p = b.product_id
            if p and p.attribute_value_ids:
                for attval in p.attribute_value_ids:
                    if attval.attribute_id.name=="Size":
                        b.product_size = attval.id
                    if attval.attribute_id.name=="Color":
                        b.product_color = attval.id
                    if attval.attribute_id.name=="Género":
                        b.product_gender = attval.id

    def _search_shop( self, operator, value ):
        shops = False
        _logger.info("_search_shop:"+str(operator)+" "+str(value))
        if value:
            shops = self.env['website_sale.shop'].search([('name',operator,value)])
            _logger.info("shops:"+str(shops))
            #self.search([('product_shop', operator, value)])
        #else:
        #    shops = self.env['website_sale.shop'].search([('name',operator,value)])
            #packs = self.search([('quant_ids', operator, value)])
            res = []
        if shops:
            res = [('product_shop', 'in', shops.ids)]
        else:
            res = []
        _logger.info("res:"+str(res))
        return res


    #product_brand = fields.Many2one("product.brand",related='product_id.product_brand_id',string="Brand",store=True)
    product_main_cat = fields.Many2one("product.category",compute="_product_main_cat",store=True)
    product_main_cat_child = fields.Many2one("product.category",compute="_product_main_cat",store=True)
    #product_size = fields.Many2one("product.attribute.value",compute="_product_size_color",store=True)
    #product_color = fields.Many2one("product.attribute.value",compute="_product_size_color",store=True)

    #product_gender = fields.Many2one("product.attribute.value",compute="_product_size_color",store=True)

    #product_company = fields.Many2one(related="product_id.company_id",string="Company",store=True,index=True)
    product_company = fields.Many2one(related="connection_account.company_id",string="Company",store=True,index=True)

    #product_shop = fields.Many2many(related="product_id.website_sale_shops",string="Shops",search='_search_shop')

class ProductecaConnectionBindingIntegration(models.Model):

    _name = "producteca.integration"
    _description = "Producteca Integration"
    _inherit = "ocapi.connection.binding"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )

    integrationId = fields.Char(string="integrationId")
    app = fields.Char(string="app")

class ProductecaConnectionBindingProductCategory(models.Model):

    _name = "producteca.category"
    _description = "Producteca Binding Category"
    _inherit = "ocapi.binding.category"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )

    name = fields.Char(string="Category",index=True)
    category_id = fields.Char(string="Category Id",index=True)
