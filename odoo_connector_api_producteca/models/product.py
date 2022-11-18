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

class product_template(models.Model):

    _inherit = "product.template"

    producteca_bindings = fields.Many2many( "producteca.binding.product_template", string="Producteca Connection Bindings" )

    def ocapi_price(self, account):
        return self.lst_price

    def ocapi_stock(self, account):
        return self.virtual_available

    def producteca_image_url_principal(self):
        return "/ocapi/producteca/img/%s/%s/%s" % (str(self.id), str(self.default_code), str("default") )

    def producteca_image_id_principal(self):
        return "%s" % ( str(self.id) )

    def producteca_image_url(self, image):
        return "/ocapi/producteca/img/%s/%s/%s" % (str(self.id), str(self.default_code), str(image.id) )

    def producteca_image_id(self, image):
        return "%s" % ( str(image.id) )

    def producteca_bind_to( self, account, bind_variants=True ):

        pt_bind = None

        for product in self:

            for bind in product.producteca_bindings:
                if (account.id in bind.connection_account.ids):
                    _logger.info("No need to add")
                    continue;

            _logger.info(_("Adding product %s to %s, bind_variants: %i") % (product.display_name, account.name, bind_variants))
            try:
                prod_binding = {
                    "connection_account": account.id,
                    "product_tmpl_id": product.id,
                    "name": product.name,
                    "description": product.description_sale,
                    "sku": product.default_code,
                    #"price": product.ocapi_price(account),
                    #"stock": product.ocapi_stock(account),
                }
                pt_bind = self.env["producteca.binding.product_template"].search([ ("product_tmpl_id","=",product.id),
                                                                                   ("connection_account","=",account.id)])
                if len(pt_bind):
                    pt_bind = pt_bind[0]
                    self.env["producteca.binding.product_template"].write([prod_binding])
                else:
                    pt_bind = self.env["producteca.binding.product_template"].create([prod_binding])

                if pt_bind:
                    product.producteca_bindings = [(4, pt_bind.id)]
                    if (bind_variants):
                        _logger.info(product.product_variant_ids)
                        for variant in product.product_variant_ids:
                            pv_bind = variant.producteca_bind_to( account, pt_bind )

            except Exception as e:
                _logger.info(e, exc_info=True)

        return pt_bind

    def producteca_unbind_from( self, account, unbind_variants=True):
        pt_bind = None

        for product in self:

            for bind in product.producteca_bindings:
                if not (account.id in bind.connection_account.ids):
                    _logger.info("No need to remove")
                    continue;

            _logger.info(_("Removing product %s to %s") % (product.display_name, account.name))
            try:
                pt_bind = self.env["producteca.binding.product_template"].search([("product_tmpl_id","=",product.id),("connection_account","=",account.id)])
                if len(pt_bind):
                    pt_bind = pt_bind[0]

                if pt_bind:
                    product.producteca_bindings = [(3, pt_bind.id)]
                    pt_bind.unlink()
                    if (unbind_variants):
                        for variant in product.product_variant_ids:
                            pv_bind = variant.producteca_unbind_from(account, pt_bind)
            except Exception as e:
                _logger.info(e, exc_info=True)

        return pt_bind

class product_product(models.Model):

    _inherit = "product.product"

    producteca_bindings = fields.Many2many( "producteca.binding.product", string="Producteca Connection Bindings" )

    def ocapi_price(self, account):
        return self.lst_price

    def _ocapi_virtual_available(self, account):

        product_id = self
        qty_available = product_id.virtual_available
        #loc_id = self._ocapi_get_location_id()

        #quant_obj = self.env['stock.quant']

        #qty_available = quant_obj._get_available_quantity(product_id, loc_id)

        return qty_available

    def ocapi_stock(self, account=None):
        stocks = []
        #ss = variant._product_available()
        sq = self.env["stock.quant"].search([('product_id','=',self.id)])
        if (sq):
            _logger.info( sq )
            #_logger.info( sq.name )
            for s in sq:
                if ( s.location_id.usage == "internal" ):
                    _logger.info( s )
                    sjson = {
                        "warehouseId": s.location_id.id,
                        "warehouse": s.location_id.display_name,
                        "quantity": s.quantity,
                        "reserved": s.reserved_quantity,
                        "available": s.quantity - s.reserved_quantity
                    }
                    stocks.append(sjson)
        return stocks

    def producteca_image_url_principal(self):
        code = self.barcode or self.default_code
        return "/ocapi/producteca/img/%s/%s/%s" % (str(self.id), str(code), str("default") )

    def producteca_image_id_principal(self):
        return "%s" % ( str(self.id) )

    def producteca_image_url(self, image):
        code = self.barcode or self.default_code
        return "/ocapi/producteca/img/%s/%s/%s" % (str(self.id), str(code), str(image.id) )

    def producteca_image_id(self, image):
        return "%s" % ( str(image.id) )

    def producteca_bind_to( self, account, binding_product_tmpl_id=False ):
        pv_bind = None

        for product in self:

            for bind in product.producteca_bindings:
                if (account.id in bind.connection_account.ids):
                    _logger.info("No need to add")
                    continue;

            _logger.info(_("Adding product %s to %s") % (product.display_name, account.name))
            try:
                prod_binding = {
                    "connection_account": account.id,
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "product_id": product.id,
                    "name": product.name,
                    "description": product.description_sale or "",
                    "sku": product.default_code or product.barcode or "",
                    #"price": product.ocapi_price(account),
                    #"stock": product.ocapi_stock(account),
                }

                #Binding Product Template if missing
                if binding_product_tmpl_id:
                    prod_binding["binding_product_tmpl_id"] = binding_product_tmpl_id.id
                else:
                    pt_bind = self.env["producteca.binding.product_template"].search([("product_tmpl_id","=",product.product_tmpl_id.id),("connection_account","=",account.id)])
                    if pt_bind and len(pt_bind):
                        prod_binding["binding_product_tmpl_id"] = pt_bind[0].id
                    else:
                        pt_bind = product.product_tmpl_id.producteca_bind_to( account, bind_variants=False )
                        if pt_bind and len(pt_bind):
                            prod_binding["binding_product_tmpl_id"] = pt_bind[0].id

                #Binding Variant finally
                pv_bind = self.env["producteca.binding.product"].search([("product_id","=",product.id),("product_tmpl_id","=",product.product_tmpl_id.id),("connection_account","=",account.id)])
                if len(pv_bind):
                    pv_bind = pv_bind[0]
                    _logger.info(prod_binding)
                    pv_bind.write(prod_binding)
                else:
                    _logger.info("Create variant binding:"+str(prod_binding))
                    pv_bind = self.env["producteca.binding.product"].create([prod_binding])

                if pv_bind:
                    product.producteca_bindings = [(4, pv_bind.id)]
                else:
                    _logger.error("Error creating variant binding: "+str(prod_binding))

            except Exception as e:
                _logger.info(e, exc_info=True)
                raise e

        return pv_bind

    def producteca_unbind_from( self, account, binding_product_tmpl_id=False):
        pv_bind = None

        for product in self:

            for bind in product.producteca_bindings:
                if not (account.id in bind.connection_account.ids):
                    _logger.info("No need to remove")
                    continue;

            _logger.info(_("Removing product %s to %s") % (product.display_name, account.name))
            try:
                pv_bind = self.env["producteca.binding.product"].search([("product_id","=",product.id),("connection_account","=",account.id)])
                if len(pv_bind):
                    pv_bind = pv_bind[0]
                    pv_bind.unlink()

                if pv_bind:
                    product.producteca_bindings = [(3, pv_bind.id)]

            except Exception as e:
                _logger.info(e, exc_info=True)

        return pv_bind

#class product_image(models.Model):

#    _inherit = "ocapi.image"

#    producteca_connection_bindings = fields.Many2many( "producteca.connection.bindings", string="Producteca Connection Bindings" )

class ProductPricelistItem(models.Model):

    _inherit = "product.pricelist.item"

    def _product_main_cat( self ):
        for b in self:
            b.product_main_cat = None
            b.product_main_cat_child = None
            p = b.product_id or b.product_tmpl_id
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
            p = b.product_id
            if p and p.attribute_value_ids:
                for attval in p.attribute_value_ids:
                    if attval.attribute_id.name=="Size":
                        b.product_size = attval.id
                    if attval.attribute_id.name=="Color":
                        b.product_color = attval.id

    def _product_brand( self ):
        related='product_id.product_brand_id'
        for b in self:
            b.product_brand = None
            p = b.product_id or b.product_tmpl_id
            if p:
                b.product_brand = p.product_brand_id

    def _product_brand_search( self, operator, value ):
        ids = []
        #if (operator == '>' or operator == '<' or operator == '=' or operator == '>=' or operator == '<='):

        #    company = self.env.user.company_id
        #    account = company.producteca_connections and company.producteca_connections[0]
        #    if not account:
        #        return []

        #    locids = account.configuration.publish_stock_locations.mapped("id")
        #    sq = self.env["stock.quant"].search([('location_id','in',locids),('quantity',operator,value)],order="quantity asc")
        #    if sq:
        #        pids = sq.mapped("product_id")
        #        vbids = self.search([('product_id','in', pids.ids)])
        #        if vbids:
        #            ids = [('id','in',vbids.ids)]

        return ids

    #product_brand = fields.Many2one("product.brand",compute="_product_brand",string="Brand",store=True)
    product_main_cat = fields.Many2one("product.category",compute="_product_main_cat",store=True)
    product_main_cat_child = fields.Many2one("product.category",compute="_product_main_cat",store=True)
    #product_size = fields.Many2one("product.attribute.value",compute="_product_size_color",store=True)
    #product_color = fields.Many2one("product.attribute.value",compute="_product_size_color",store=True)
    producteca_tmpl_bindings = fields.Many2many(string="Product Template Bindings",related='product_tmpl_id.producteca_bindings')
    producteca_var_bindings = fields.Many2many(string="Product Variant Bindings",related='product_id.producteca_bindings')
    #website_sale_shops = fields.Many2many(related="product_tmpl_id.website_sale_shops",string="Shops")

    #product_default_code = fields.Char(related="product_id.default_code",string="Sku")
    #product_barcode = fields.Char(related="product_id.barcode",string="Barcode")
