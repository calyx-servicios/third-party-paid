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

#from .warning import warning
import requests
from odoo.addons.meli_oerp.melisdk.meli import Meli
from odoo.addons.meli_oerp.models.versions import *

class product_product(models.Model):

    _inherit = "product.product"

    def _meli_update_logistic_type(self, meli_id=None, meli=False, config=False):
        company = self.env.user.company_id
        product = self
        config = config or company
        company = (config and 'company_id' in config._fields and config.company_id) or company

        meli_util_model = self.env['meli.util']
        if not meli:
            meli = meli_util_model.get_new_instance(company)

        meli_id = meli_id or product.meli_id

        if not meli_id:
            return {}

        try:
            response = meli.get("/items/"+str(meli_id), {'access_token':meli.access_token})
            rjson = response.json()
        except IOError as e:
            _logger.info( "I/O error({0}): {1}".format(e.errno, e.strerror) )
            return {}
        except:
            _logger.info( "Rare error" )
            return {}

        if (rjson and "shipping" in rjson and "logistic_type" in rjson["shipping"]):
            meli_shipping_logistic_type = rjson["shipping"]["logistic_type"]
            if meli_id==product.meli_id:
                product.meli_shipping_logistic_type = meli_shipping_logistic_type

            return meli_shipping_logistic_type
        return ""

    def _meli_get_location_id(self, meli_id=None, meli=False, config=None):

        loc_id = False
        company = self.env.user.company_id
        config = config or company
        company = (config and 'company_id' in config._fields and config.company_id) or company
        meli_id = meli_id or self.meli_id
        meli_shipping_logistic_type = self._meli_update_logistic_type(meli_id=meli_id, meli=meli,config=config)

        if (config.mercadolibre_stock_warehouse):
            loc_id = config.mercadolibre_stock_warehouse.lot_stock_id

        if (config.mercadolibre_stock_location_to_post):
            loc_id = config.mercadolibre_stock_location_to_post
        else:
            #loc_id = self.env["stock.location"].search([('mercadolibre_active','=',True),('company_id', '=', company.id)])
            loc_id = self.env["stock.location"].search([('mercadolibre_active','=',True),('company_id', '=', company.id)])
            if loc_id and len(loc_id)==0:
                loc_id = False
            if "mercadolibre_stock_location_to_post_many" in config._fields and config.mercadolibre_stock_location_to_post_many:
                loc_id = []
                for lid in config.mercadolibre_stock_location_to_post_many:
                    loc_id.append(lid)
                #_logger.info(loc_id)


        if (meli_shipping_logistic_type == "fulfillment"):
            if (config.mercadolibre_stock_warehouse_full):
                loc_id = config.mercadolibre_stock_warehouse_full.lot_stock_id
            if (config.mercadolibre_stock_location_to_post_full):
                loc_id = config.mercadolibre_stock_location_to_post_full

        return loc_id

    #virtual available from this variant in locations defined on configuration (see _meli_get_location_id)
    def _meli_virtual_available(self, order=None, meli_id=None, meli=False, config=None):

        product_id = self
        company = self.env.user.company_id
        config = config or company
        company = (config and 'company_id' in config._fields and config.company_id) or company
        meli_id = meli_id or self.meli_id
        loc_id = self._meli_get_location_id( meli_id=meli_id, meli=meli,config=config)

        #_logger.info("meli_oerp_stock._meli_virtual_available loc_id: "+str(loc_id))

        quant_obj = self.env['stock.quant']
        #_logger.info("meli_oerp_stock._meli_virtual_available quant_obj: "+str(quant_obj)+" product_id:"+str(product_id))

        qty_available = 0
        #_logger.info("meli_oerp_stock._meli_virtual_available quant_obj: "+str(quant_obj)+" product_id:"+str(product_id))
        for loc in loc_id:
            if ("mercadolibre_stock_virtual_available" in config._fields and (not config.mercadolibre_stock_virtual_available or config.mercadolibre_stock_virtual_available=='virtual')):
            #_logger.info(loc.display_name)
            #if 1==1:
                qty_available+= quant_obj._get_available_quantity(product_id, loc)
            else:
                qty_available+= product_id.get_theoretical_quantity( product_id.id, loc.id )
                #qty_available+= product_id.qty_available
            _logger.info("qty_available:"+str(qty_available))
        #_logger.info("meli_oerp_stock._meli_virtual_available qty_available: "+str(qty_available))

        return qty_available

    def _meli_available_quantity( self, meli_id=None, meli=False, config=None ):

        #_logger.info("meli_oerp_stock._meli_available_quantity")
        product = self
        product_tmpl = product.product_tmpl_id
        new_meli_available_quantity = product.meli_available_quantity

        meli_id = meli_id or self.meli_id
        #_logger.info("meli_oerp_stock._meli_virtual_available "+str(product._meli_virtual_available()))
        virtual_av = product._meli_virtual_available( meli_id=meli_id, meli=meli, config=config )
        new_meli_available_quantity = virtual_av

        # Chequea si es fabricable
        product_fab = False
        if (1==1 and virtual_av<=0 and product.route_ids):
            for route in product.route_ids:
                if (route.name in ['Fabricar','Manufacture']):
                    #raise ValidationError("Fabricar")
                    #product.meli_available_quantity = product.meli_available_quantity
                    #_logger.info("Fabricar:"+str(new_meli_available_quantity))
                    product_fab = True
            if (not product_fab and product._meli_virtual_available( meli_id=meli_id, meli=meli, config=config )==0):
                new_meli_available_quantity = product._meli_virtual_available( meli_id=meli_id, meli=meli, config=config )

        if (1==1 and 'mrp.bom' in self.env and new_meli_available_quantity<=10000):
            _logger.info("search bom:"+str(product.default_code))
            bom_id = self.env['mrp.bom'].search([('product_id','=',product.id)],limit=1)
            if not bom_id:
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id','=',product_tmpl.id)],limit=1)
            if bom_id and bom_id.type == 'phantom':
                #_logger.info(bom_id.type)
                _logger.info("bom_id:"+str(bom_id))
                #chequear si el componente principal es fabricable
                stock_material_max = 100000
                stock_material = 0
                new_meli_available_quantity = 0
                for bom_line in bom_id.bom_line_ids:
                    #if (bom_line.product_id.default_code.find(product_tmpl.code_prefix)==0):
                    if (bom_line.product_id):
                        #_logger.info(product_tmpl.code_prefix)
                        _logger.info("bom product: " + str(bom_line.product_id.default_code) )
                        for route in product.route_ids:
                            if (route.name in ['Fabricar','Manufacture']):
                                #_logger.info("Fabricar")
                                new_meli_available_quantity = 1
                            if (route.name in ['Comprar','Buy']):
                                #_logger.info("Comprar")
                                virtual_comp_av = bom_line.product_id._meli_virtual_available( meli_id=meli_id, meli=meli,config=config)
                                _logger.info("bom component stock: " + str(virtual_comp_av) )
                                stock_material = virtual_comp_av / bom_line.product_qty
                                if stock_material>=0 and stock_material<=stock_material_max:
                                    stock_material_max = stock_material
                                    new_meli_available_quantity = stock_material_max
                                    _logger.info("stock based on minimum material available / " +str(bom_line.product_qty)+ ": " + str(new_meli_available_quantity))

        return new_meli_available_quantity

    def product_update_stock(self, stock=False, meli=False, config=None):
        product = self
        uomobj = self.env[uom_model]
        _stock = product.virtual_available

        try:
            if (stock!=False):
                _stock = stock
                if (_stock<0):
                    _stock = 0

            if (product.default_code):
                product.set_bom()

            if (product.meli_default_stock_product):
                _stock = product.meli_default_stock_product._meli_available_quantity(meli=meli,config=config)
                if (_stock<0):
                    _stock = 0

            if (1==1 and _stock>=0 and product._meli_available_quantity(meli=meli,config=config)!=_stock):
                _logger.info("Updating stock for variant." + str(_stock) )
                #wh = self.env['stock.location'].search([('usage','=','internal')]).id
                wh = product._meli_get_location_id(meli_id=product.meli_id,meli=meli,config=config)
                _logger.info("Updating stock for variant. location: " + str(wh and wh.display_name) )
                #product_uom_id = uomobj.search([('name','=','Unidad(es)')])
                #if (product_uom_id.id==False):
                #    product_uom_id = 1
                #else:
                #    product_uom_id = product_uom_id.id
                product_uom_id = product.uom_id and product.uom_id.id

                stock_inventory_fields = get_inventory_fields(product, wh)

                _logger.info("stock_inventory_fields:")
                _logger.info(stock_inventory_fields)
                StockInventory = self.env['stock.inventory'].create(stock_inventory_fields)
                #_logger.info("StockInventory:")
                #_logger.info(StockInventory)
                if (StockInventory):
                    stock_inventory_field_line = {
                        "product_qty": _stock,
                        'theoretical_qty': 0,
                        "product_id": product.id,
                        "product_uom_id": product_uom_id,
                        "location_id": wh and wh.id,
                        #'inventory_location_id': wh and wh.id,
                        "inventory_id": StockInventory.id,
                        #"name": "INV "+ nombre
                        #"state": "confirm",
                    }
                    StockInventoryLine = self.env['stock.inventory.line'].create(stock_inventory_field_line)
                    #print "StockInventoryLine:", StockInventoryLine, stock_inventory_field_line
                    _logger.info("StockInventoryLine:")
                    _logger.info(stock_inventory_field_line)
                    if (StockInventoryLine):
                        return_id = stock_inventory_action_done(StockInventory)
                        _logger.info("action_done:"+str(return_id))
        except Exception as e:
            _logger.info("product_update_stock Exception")
            _logger.info(e, exc_info=True)
