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
###############################################*###############################

from odoo import fields, osv, models, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
import pdb
from .warning import warning
import requests

from . import versions
from .versions import *
import hashlib
from odoo.exceptions import UserError, ValidationError

class ProductecaConnectionAccount(models.Model):

    _name = "producteca.account"
    _description = "Producteca Account"
    _inherit = "ocapi.connection.account"

    configuration = fields.Many2one( "producteca.configuration", string="Configuration", help="Connection Parameters Configuration"  )
    #type = fields.Selection([("custom","Custom"),("producteca","Producteca")],string='Connector',index=True)
    type = fields.Selection(selection_add=[("producteca","Producteca")],
				string='Connector Type',
				default="producteca",
				ondelete={'producteca': 'set default'},
				index=True)
    country_id = fields.Many2one("res.country",string="Country",index=True)

    producteca_product_template_bindings = fields.One2many( "producteca.binding.product_template", "connection_account", string="Product Bindings" )
    producteca_product_bindings = fields.One2many( "producteca.binding.product", "connection_account", string="Product Variant Bindings" )
    producteca_orders = fields.One2many( "producteca.sale_order", "connection_account", string="Orders" )

    def create_credentials(self, context=None):
        context = context or self.env.context
        _logger.info("create_credentials: " + str(context))

        now = datetime.now()
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        base_str = str(self.name) + str(date_time)

        hash = hashlib.md5(base_str.encode())
        hexhash = hash.hexdigest()

        self.client_id = hexhash

        base_str = str(self.name) +str(self.client_id) + str(date_time)

        hash = hashlib.md5(base_str.encode())
        hexhash = hash.hexdigest()

        self.secret_key = hexhash

    def list_data(self, **post):
        offset = post.get("offset") or 0
        limit = post.get("limit") or 1000
        data = {
            'paging': {
                'total': 0,
                'limit': limit,
                'offset': offset
            },
            'results': []
        }
        return data, limit, offset

    def list_catalog( self, **post ):

        data, limit, offset = self.list_data(**post)
        result = []

        _logger.info("list_catalog producteca")
        #_logger.info(result)

        account = self
        company = account.company_id or self.env.user.company_id

        total = self.env["producteca.binding.product"].search_count([("connection_account","=",account.id)])
        bindings = self.env["producteca.binding.product"].search([("connection_account","=",account.id)], limit=limit, offset=offset)
        offset2 = (bindings and min( offset+limit, total ) ) or str(offset+limit)

        #start notification
        noti = None
        logs = ""
        errors = ""

        try:
            internals = {
                "connection_account": account,
                "application_id": account.client_id or '',
                "user_id": account.seller_id or '',
                "topic": "catalog",
                "resource": "list_catalog ["+str(offset)+"-"+str(offset2)+str("]/")+str(total),
                "state": "PROCESSING"
            }
            noti = self.env["producteca.notification"].start_internal_notification( internals )
        except Exception as e:
            _logger.error("list_catalog error creating notification: "+str(e))
            pass;

        for binding in bindings:

            product = binding.product_tmpl_id

            tpl = {
                "name": product.name or "",
                "code": product.default_code or "",
                "barcode": product.barcode or "",
                "brand": ("product_brand_id" in product._fields and product.product_brand_id and product.product_brand_id.name) or '',
                "variations": [],
                "category": product.categ_id.name or "",
                "notes": product.description_sale or "",
                "prices": [],
                "dimensions": {
                    "weight": ('weight' in self.env['product.product']._fields and product.weight) or 1,
                    "width": 1,
                    "length": 1,
                    "height": 1,
                    "pieces": 1
                },
                "attributes": []
            }

            prices = []
            #self.with_context(pricelist=pricelist.id).price
            #for plitem in product.item_ids:
            for pl in account.configuration.publish_price_lists:
                plprice = product.with_context(pricelist=pl.id).price
                price = {
                    "priceListId": pl.id,
                    "priceList": pl.name,
                    "amount": plprice,
                    "currency": pl.currency_id.name
                }
                prices.append(price)

            attributes = []
            attvariants = []
            for attline in product.attribute_line_ids:
                if len(attline.value_ids)>1:
                    attvariants.append(attline.attribute_id.id)
                else:
                    for val in attline.value_ids:
                        att = {
                            "key": attline.attribute_id.name,
                            "value": val.name
                        }
                        attributes.append(att)

            #tpl["variations"]
            for variant in product.product_variant_ids:

                var = {
                    "sku": variant.default_code or "",
                    #"color": "" or "",
                    #"size": "" or "",
                    "barcode": variant.barcode or "",
                    "code": variant.default_code or "",
                }

                for val in variant.attribute_value_ids:
                    if val.attribute_id.id in attvariants:
                        var[val.attribute_id.name] = val.name

                stocks = []
                #ss = variant._product_available()
                #_logger.info("account.configuration.publish_stock_locations")
                #_logger.info(account.configuration.publish_stock_locations.mapped("id"))
                sq = self.env["stock.quant"].search([('product_id','=',variant.id)])
                if (sq):
                    #_logger.info( sq )
                    #_logger.info( sq.name )
                    for s in sq:
                        #TODO: filtrar por configuration.locations
                        #TODO: merge de stocks
                        #TODO: solo publicar available
                        if ( s.location_id.usage == "internal" and s.location_id.id in account.configuration.publish_stock_locations.mapped("id")):
                            _logger.info( s )
                            sjson = {
                                "warehouseId": s.location_id.id,
                                "warehouse": s.location_id.display_name,
                                "quantity": s.quantity,
                                "reserved": s.reserved_quantity,
                                "available": s.quantity - s.reserved_quantity
                            }
                            stocks.append(sjson)

                #{
                #    "warehouseId": 61879,
                #    "warehouse": "Estoque Principal - Ecommerce",
                #    "quantity": 0,
                #    "reserved": 0,
                #    "available": 0
                #}

                pictures = []
                if "product_image_ids" in variant._fields:
                    if variant.image:
                        img = {
                            "url": variant.producteca_image_url_principal(),
                            "id": variant.producteca_image_id_principal()
                        }
                        pictures.append(img)
                    for image in variant.product_image_ids:
                        img = {
                            "url": variant.producteca_image_url(image),
                            "id": variant.producteca_image_id(image)
                        }
                        pictures.append(img)

                var["pictures"] = pictures
                var["stocks"] = stocks

                tpl["variations"].append(var)

            tpl["prices"] = prices
            tpl["attributes"] = attributes

            result.append(tpl)

        if noti:
            logs = str(result)
            noti.stop_internal_notification(errors=errors,logs=logs)

        data["paging"]["total"] = total
        data["results"] = result
        return data

    def list_pricestock( self, **post ):
        _logger.info("list_pricestock")
        data, limit, offset = self.list_data(**post)
        result = []

        account = self
        company = account.company_id or self.env.user.company_id

        total = self.env["producteca.binding.product"].search_count([("connection_account","=",account.id)])
        bindings = self.env["producteca.binding.product"].search([("connection_account","=",account.id)], limit=limit, offset=offset)
        offset2 = (bindings and min( offset+limit, total ) ) or str(offset+limit)

        #start notification
        noti = None
        logs = ""
        errors = ""
        try:
            internals = {
                "connection_account": account,
                "application_id": account.client_id or '',
                "user_id": account.seller_id or '',
                "topic": "catalog",
                "resource": "list_pricestock ["+str(offset)+"-"+str(offset2)+str("]/")+str(total),
                "state": "PROCESSING"
            }
            noti = self.env["producteca.notification"].start_internal_notification( internals )
        except Exception as e:
            _logger.error("list_pricestock error creating notification: "+str(e))
            pass;

        for binding in bindings:

            variant = binding.product_id

            var = {
                "sku": variant.default_code or "",
                "barcode": variant.barcode or "",
            }

            stocks = []
            #ss = variant._product_available()
            sq = self.env["stock.quant"].search([('product_id','=',variant.id)])
            if (sq):
                #_logger.info( sq )
                #_logger.info( sq.name )
                for s in sq:
                    if ( s.location_id.usage == "internal" and s.location_id.id in account.configuration.publish_stock_locations.mapped("id")):
                        _logger.info( s )
                        sjson = {
                            "warehouseId": s.location_id.id,
                            "warehouse": s.location_id.display_name,
                            "quantity": s.quantity,
                            "reserved": s.reserved_quantity,
                            "available": s.quantity - s.reserved_quantity
                        }
                        stocks.append(sjson)

            var["stocks"] = stocks

            prices = []
            for pl in account.configuration.publish_price_lists:
                plprice = variant.with_context(pricelist=pl.id).price
                price = {
                    "priceListId": pl.id,
                    "priceList": pl.name,
                    "amount": plprice,
                    "currency": pl.currency_id.name
                }
                prices.append(price)
            var["prices"] = prices

            result.append(var)

        if noti:
            logs = str(result)
            noti.stop_internal_notification(errors=errors,logs=logs)

        data["paging"]["total"] = total
        data["results"] = result
        return data

    def list_pricelist( self, **post ):
        _logger.info("list_pricelist")
        data, limit, offset = self.list_data(**post)
        result = []

        account = self
        company = account.company_id or self.env.user.company_id

        total = self.env["producteca.binding.product"].search_count([("connection_account","=",account.id)])
        bindings = self.env["producteca.binding.product"].search([("connection_account","=",account.id)], limit=limit, offset=offset)
        offset2 = (bindings and min( offset+limit, total ) ) or str(offset+limit)

        #start notification
        noti = None
        logs = ""
        errors = ""
        try:
            internals = {
                "connection_account": account,
                "application_id": account.client_id or '',
                "user_id": account.seller_id or '',
                "topic": "catalog",
                "resource": "list_pricelist ["+str(offset)+"-"+str(offset2)+str("]/")+str(total),
                "state": "PROCESSING"
            }
            noti = self.env["producteca.notification"].start_internal_notification( internals )
        except Exception as e:
            _logger.error("list_pricelist error creating notification: "+str(e))
            pass;

        for binding in bindings:

            variant = binding.product_id

            var = {
                "sku": variant.default_code or "",
                "barcode": variant.barcode or "",
            }

            prices = []
            for pl in account.configuration.publish_price_lists:
                plprice = variant.with_context(pricelist=pl.id).price
                price = {
                    "priceListId": pl.id,
                    "priceList": pl.name,
                    "amount": plprice,
                    "currency": pl.currency_id.name
                }
                prices.append(price)
            var["prices"] = prices

            result.append(var)

        if noti:
            logs = str(result)
            noti.stop_internal_notification(errors=errors,logs=logs)

        data["paging"]["total"] = total
        data["results"] = result
        return data

    def list_stock( self, **post ):
        _logger.info("list_stock")
        data, limit, offset = self.list_data(**post)
        result = []

        account = self
        company = account.company_id or self.env.user.company_id

        total = self.env["producteca.binding.product"].search_count([("connection_account","=",account.id)])
        bindings = self.env["producteca.binding.product"].search([("connection_account","=",account.id)], limit=limit, offset=offset)
        offset2 = (bindings and min( offset+limit, total ) ) or str(offset+limit)

        #start notification
        noti = None
        logs = ""
        errors = ""
        try:
            internals = {
                "connection_account": account,
                "application_id": account.client_id or '',
                "user_id": account.seller_id or '',
                "topic": "catalog",
                "resource": "list_stock ["+str(offset)+"-"+str(offset2)+str("]/")+str(total),
                "state": "PROCESSING"
            }
            noti = self.env["producteca.notification"].start_internal_notification( internals )
        except Exception as e:
            _logger.error("list_stock error creating notification: "+str(e))
            pass;

        for binding in bindings:

            variant = binding.product_id

            var = {
                "sku": variant.default_code or "",
                "barcode": variant.barcode or "",
            }


            stocks = []
            #ss = variant._product_available()
            sq = self.env["stock.quant"].search([('product_id','=',variant.id)])
            if (sq):
                #_logger.info( sq )
                #_logger.info( sq.name )
                for s in sq:
                    if ( s.location_id.usage == "internal" and s.location_id.id in account.configuration.publish_stock_locations.mapped("id")):
                        _logger.info( s )
                        sjson = {
                            "warehouseId": s.location_id.id,
                            "warehouse": s.location_id.display_name,
                            "quantity": s.quantity,
                            "reserved": s.reserved_quantity,
                            "available": s.quantity - s.reserved_quantity
                        }
                        stocks.append(sjson)

            var["stocks"] = stocks

            result.append(var)

        if noti:
            logs = str(result)
            noti.stop_internal_notification(errors=errors,logs=logs)

        data["paging"]["total"] = total
        data["results"] = result
        return data

    def street(self, contact, billing=False ):
        street_str = ""
        if not billing and "location_streetName" in contact:
            sName = "location_streetName" in contact and contact["location_streetName"]
            sNumber = "location_streetNumber" in contact and contact["location_streetNumber"]
            street_str = sName
            if sNumber:
                street_str = sName+" "+str(sNumber)
        else:
            #contact["billingInfo_streetName"]+" "+contact["billingInfo_streetNumber"]
            sName = "billingInfo_streetName" in contact and contact["billingInfo_streetName"]
            sNumber = "billingInfo_streetNumber" in contact and contact["billingInfo_streetNumber"]
            street_str = sName
            if sNumber:
                street_str = sName+" "+str(sNumber)
        return street_str

    def city(self, contact, billing=False ):
        if not billing and "location_city" in contact:
            return ("location_city" in contact and contact["location_city"])
        else:
            return ("billingInfo_city" in contact and contact["billingInfo_city"])


    #return odoo country id
    def country(self, contact, billing=False ):
        #Producteca country has no country? ok
        #take country from account company if not available
        country = False
        if not billing and "country" in contact and len(contact["country"]):
            country = contact["country"]
        else:
            country = ("billingInfo_country" in contact and contact["billingInfo_country"])
            #do something
        if country:
            countries = self.env["res.country"].search([("name","like",country)])
            if countries and len(countries):
                return countries[0].id

        company = self.company_id or self.env.user.company_id
        country = self.country_id or company.country_id

        return country.id

    def ostate(self, country, contact, billing=False ):
        full_state = ''

        #parse from Producteca contact
        Receiver = {}
        Receiver.update(contact)
        _logger.info("ostate >> contact:"+str(contact))
        _logger.info("ostate >> Receiver:"+str(Receiver))
        if not billing:
            Receiver["state"] = { "name": ("location_state" in contact and contact["location_state"]) or "", "id": ("location_stateId" in contact and contact["location_stateId"]) or '' }
        else:
            Receiver["state"] = { "name": ("billingInfo_state" in contact and contact["billingInfo_state"]) or "", "id": ("billingInfo_stateId" in contact and contact["billingInfo_stateId"]) or '' }

        country_id = country

        state_id = False
        if (Receiver and 'state' in Receiver):
            if ('id' in Receiver['state'] and Receiver['state']['id']):
                state = self.env['res.country.state'].search([('code','like',Receiver['state']['id']),('country_id','=',country_id)])
                if (len(state)):
                    state_id = state[0].id
                    return state_id
                id_producteca = Receiver['state']['id']
                if id_producteca:
                    id = id_producteca
                    state = self.env['res.country.state'].search([('code','like',id),('country_id','=',country_id)])
                    if (len(state)):
                        state_id = state[0].id
                        return state_id
                id_ml = False
                #id_ml = Receiver['state']['id'].split("-")
                #_logger.info(Receiver)
                #_logger.info(id_ml)
                if (id_ml and len(id_ml)==2):
                    id = id_ml[1]
                    state = self.env['res.country.state'].search([('code','like',id),('country_id','=',country_id)])
                    if (len(state)):
                        state_id = state[0].id
                        return state_id
            if ('name' in Receiver['state']):
                full_state = Receiver['state']['name']
                state = self.env['res.country.state'].search(['&',('name','like',full_state),('country_id','=',country_id)])
                if (len(state)):
                    state_id = state[0].id
        return state_id

    def full_phone(self, contact, billing=False ):
        return contact["phoneNumber"]

    def doc_info(self, contactfields, doc_undefined=None):
        dinfo = {}
        if "billingInfo_docNumber" in contactfields and 'billingInfo_docType' in contactfields:

            doc_number = contactfields["billingInfo_docNumber"]
            doc_type = contactfields['billingInfo_docType']

            if (doc_type and ('afip.responsability.type' in self.env) and doc_number ):
                doctypeid = self.env['res.partner.id_category'].search([('code','=',doc_type)]).id
                if (doctypeid):
                    dinfo['main_id_category_id'] = doctypeid
                    dinfo['main_id_number'] = doc_number
                    if (doc_type=="CUIT"):
                        #IVA Responsable Inscripto
                        afipid = self.env['afip.responsability.type'].search([('code','=',1)]).id
                        #dinfo["afip_responsability_type_id"] = afipid
                    else:
                        #if (Buyer['billing_info']['doc_type']=="DNI"):
                        #Consumidor Final
                        afipid = self.env['afip.responsability.type'].search([('code','=',5)]).id
                        dinfo["afip_responsability_type_id"] = afipid
                else:
                    _logger.error("res.partner.id_category:" + str(doc_type))
            else:
                #use doc_undefined
                if doc_undefined:

                    if ('afip.responsability.type' in self.env):
                        afipid = self.env['afip.responsability.type'].search([('code','=',5)]).id
                        dinfo["afip_responsability_type_id"] = afipid

                    doctypeid = self.env['res.partner.id_category'].search([('code','=','DNI')]).id
                    dinfo['main_id_category_id'] = doctypeid
                    dinfo['main_id_number'] = doc_undefined
        return dinfo

    def ocapi_price_unit( self, product=False, price=0, tax_id=False ):

        account = self
        company = account.company_id or self.env.user.company_id
        config = account.configuration

        product_template = product.product_tmpl_id
        ml_price_converted = float(price)
        tax_excluded = True
        if ( tax_excluded and product_template.taxes_id ):
            txfixed = 0
            txpercent = 0
            tax_ids = tax_id or product_template.taxes_id
            _logger.info("Adjust taxes: "+str(tax_ids))
            for txid in tax_ids:
                if not txid.company_id or (company and txid.company_id.id==company.id):
                    if (txid.type_tax_use=="sale" and not txid.price_include):
                        if (txid.amount_type=="percent"):
                            _logger.info("Percent: "+str(txid)+" "+str(txid.amount))
                            txpercent = txpercent + txid.amount
                        if (txid.amount_type=="fixed"):
                            _logger.info("Fixed: "+str(txid)+" "+str(txid.amount))
                            txfixed = txfixed + txid.amount
                        _logger.info(txid.amount)
            if (txfixed>0 or txpercent>0):
                ml_price_converted = txfixed + ml_price_converted / (1.0 + txpercent*0.01)
                _logger.info("From: "+str(price)+" with Tx Total:"+str(txpercent)+" to Price:"+str(ml_price_converted))
                #_logger.info("Price adjusted with taxes:"+str(ml_price_converted))

        ml_price_converted = round(ml_price_converted,2)
        return ml_price_converted

    def import_sales( self, **post ):

        _logger.info("import_sales")
        account = self
        company = account.company_id or self.env.user.company_id
        noti = None
        logs = ""
        errors = ""

        result = []
        if (account and not account.configuration):
            result.append({"error": "No account configuration. Check Producteca account configuration. "})
            return result

        if (account and account.configuration and account.configuration.import_sales==False):
            result.append({"error": "field: 'import_sales' not enabled. Check Producteca account configuration. "})
            return result

        #start notification
        try:
            internals = {
                "connection_account": self,
                "application_id": self.client_id or '',
                "user_id": self.seller_id or '',
                "topic": "sales",
                "resource": "import_sales",
                "state": "PROCESSING"
            }
            noti = self.env["producteca.notification"].start_internal_notification( internals )
        except Exception as e:
            _logger.error("import_sales error creating notification: "+str(e))
            pass;

        result = []

        sales = post.get("sales")
        logs = str(sales)

        _logger.info("Processing sales")

        for sale in sales:
            res = self.import_sale( sale, noti )
            for r in res:
                result.append(r)

        #close notifications
        if noti:
            errors = str(result)
            logs = str(logs)
            noti.stop_internal_notification(errors=errors,logs=logs)

        _logger.info(result)
        return result

    def import_sale( self, sale, noti ):

        account = self
        company = account.company_id or self.env.user.company_id
        config = account and account.configuration
        saleorderline_obj = self.env['sale.order.line']
        result = []
        pso = False
        psoid = False
        so = False

        _logger.info(sale)
        psoid = sale["id"]

        if not psoid:
            return result
        fields = {
            "conn_id": psoid,
            "connection_account": account.id,
            "name": "PR-"+str(psoid)
        }
        #"warehouseIntegration"
        key_bind = ["channel","tags","integrations","cartId",
                    "warehouse","amount","couponAmount",
                    "shippingCost","financialCost","paidApproved",
                    "paymentStatus","deliveryStatus","paymentFulfillmentStatus",
                    "deliveryFulfillmentStatus","deliveryMethod","paymentTerm",
                    "currency","customId","isOpen",
                    "isCanceled","hasAnyShipments","date","logisticType","shippingLink"]
        for k in key_bind:
            key = k
            if key in sale:
                val = sale[key]
                if type(val)==dict:
                    for skey in val:
                        fields[key+"_"+skey] = val[skey]
                elif type(val)==list and len(val):
                    for valL in val:
                        #valL = val[ikey]
                        if type(valL)==dict:
                            for skey in valL:
                                if str(key+"_"+skey) in fields:
                                    fields[key+"_"+skey]+= ","+str(valL[skey])
                                else:
                                    fields[key+"_"+skey] = str(valL[skey])

                else:
                    if key =="date":
                        val = ml_datetime(val)
                    fields[key] = val

        _logger.info(fields)
        _logger.info("Searching sale order: " + str(psoid))
        noti.resource = 'import_sales/'+fields['name']

        pso = self.env["producteca.sale_order"].sudo().search( [( 'conn_id', '=', psoid ),
                                                                ("connection_account","=",account.id)] )

        #use producteca channel and integrations data to set Order Name
        chan = None
        chanbinded = None
        if "producteca.channel" in self.env:
            iapp = 0
            if "integrations_app" in fields and fields["integrations_app"] and len(fields["integrations_app"]):
                appids = [int(s) for s in fields["integrations_app"].split() if s.isdigit()]
                if len(appids):
                    iapp = appids[0]
                if iapp==0:
                    appids = [int(s) for s in fields["integrations_app"].split(",") if s.isdigit()]
                    if len(appids):
                        iapp = appids[0]
                _logger.info("appids:"+str(appids))
                _logger.info("iapp:"+str(iapp))
                if iapp>0:
                    chan = self.env["producteca.channel"].search([ ("app_id", "=", str(iapp) ) ], limit=1)
                else:
                    _logger.error("integrations_app:"+str(fields["integrations_app"]))

            if not chan:
                #chan = self.env["producteca.channel"].search([], limit=1)
                return { "error": "channel not found" }

        if chan:

            cartId = ("cartId" in fields and fields["cartId"])
            integId = ("integrations_integrationId" in fields and fields["integrations_integrationId"])
            integId = cartId or integId
            _logger.info("integId:"+str(integId))

            chanbinded = config.producteca_channels_bindings and config.producteca_channels_bindings.filtered(lambda b: (b.channel_id and b.channel_id.id == chan.id))
            chanbinded and fields.update( { "channel_binding_id": chanbinded.id } )

            fields.update( { 'name': "PR-"+str(psoid)+ "-" + str((chanbinded and chanbinded.code) or (chan and chan.code))+"-"+str(integId) } )
            fields.update( { 'channel_id': chan.id } )
            _logger.info(fields['name'])

            noti.resource = 'import_sales/'+fields['name']

        including_shipping_cost = (chanbinded and chanbinded.including_shipping_cost) or (config and config.including_shipping_cost) or "always"


        #create/update sale order
        _logger.info(pso)
        so_bind_now = None
        if not pso:
            _logger.info("Creating producteca order")
            pso = self.env["producteca.sale_order"].sudo().create( fields )
        else:
            _logger.info("Updating producteca order")
            pso.write( fields )

        if not pso:
            error = {"error": "Sale Order creation error"}
            result.append(error)
            if so:
                so.message_post(body=str(error["error"]))
            return result
        else:
            noti.producteca_sale_order = pso.id

        #set producteca bindings
        sqls = 'select producteca_sale_order_id, sale_order_id from producteca_sale_order_sale_order_rel where producteca_sale_order_id = '+str(pso.id)
        _logger.info("Search Producteca Sale Order Binding "+str(sqls))
        respb = self._cr.execute(sqls)
        _logger.info(respb)
        restot = self.env.cr.fetchall()
        if len(restot)==0:
            so_bind_now = [(4, pso.id, 0)]
        else:
            _logger.info("sale order id:"+str(restot[0][1]))
            so = self.env["sale.order"].browse([restot[0][1]])

        #create contact
        contactkey_bind = ["name","contactPerson","mail",
                    "phoneNumber","taxId","location",
                    "type","profile",
                    #"billingInfo",
                    "id"]

        #process "contact"
        partner_id = False
        client = False
        if "contact" in sale:
            contact = sale["contact"]
            id = contact["id"]
            contactfields = {
                "conn_id": str(id),
                "connection_account": account.id
            }
            for k in contactkey_bind:
                key = k
                if key in contact:
                    val = contact[key]
                    if type(val)==dict:
                        for skey in val:
                            if (not (skey=="country") and not (skey=="nickname")):
                                contactfields[key+"_"+skey] = val[skey]
                    else:
                        contactfields[key] = val

            _logger.info(contactfields)
            _logger.info("Searching Producteca Client: " + str(id))
            client = self.env["producteca.client"].sudo().search([( 'conn_id', '=', str(id) ),
                                                                ("connection_account","=",account.id)])
            if not client:
                _logger.info("Creating producteca client")
                client = self.env["producteca.client"].sudo().create( contactfields )
            else:
                if len(client)>1:
                    client = client[0]
                _logger.info("Updating producteca client")
                if ('location_stateId' in contactfields) or ('billingInfo_stateId' in contactfields):
                    client.write( { 'location_stateId': ('location_stateId' in contactfields and contactfields['location_stateId']),'billingInfo_stateId': ('billingInfo_stateId' in contactfields and contactfields['billingInfo_stateId']) } )
            if not client:
                error = {"error": "Producteca Client creation error"}
                result.append(error)
                if so:
                    so.message_post(body=str(error["error"]))
                return result
            else:
                if client.partner_id:
                    partner_id = client.partner_id
                pso.write({ "client": client.id, "mail": client.mail })

            #partner_id = self.env["res.partner"].search([  ('producteca_bindings','in',[id] ) ] )
            sqls = 'select producteca_client_id, res_partner_id from producteca_client_res_partner_rel where producteca_client_id = '+str(client.id)
            _logger.info("Search Partner Binding "+str(sqls))
            respb = self._cr.execute(sqls)
            _logger.info(respb)
            restot = self.env.cr.fetchall()

            country_id = self.country(contact=contactfields)

            buyer_name = ("name" in contactfields and contactfields["name"])
            firstName = ("billingInfo_firstName" in contactfields and contactfields["billingInfo_firstName"])
            lastName = ("billingInfo_lastName" in contactfields and contactfields["billingInfo_lastName"])
            if not buyer_name and firstName and lastName:
                _logger.info("buyer_name using first and last: firstName:['"+str(firstName)+"'] lastName['"+str(lastName)+"']")
                buyer_name = firstName + str(" ") + lastName
            if not firstName and not lastName and 'contactPerson' in contactfields:
                buyer_name = contactfields['contactPerson']

            billingInfo_businessName = ("billingInfo_businessName" in contactfields and contactfields["billingInfo_businessName"])
            if billingInfo_businessName and len(billingInfo_businessName)>1:
                buyer_name = billingInfo_businessName

            ocapi_buyer_fields = {
                "name": buyer_name,
                'street': self.street(contact=contactfields,billing=True) or self.street(contact=contactfields),
                'street2': ("billingInfo_neighborhood" in contactfields and contactfields["billingInfo_neighborhood"]) or str("location_neighborhood" in contactfields and contactfields["location_neighborhood"]),
                'city': self.city(contact=contactfields,billing=True) or self.city(contact=contactfields),
                'country_id': country_id,
                'state_id': self.ostate( country=country_id, contact=contactfields,billing=True ) or self.ostate( country=country_id, contact=contactfields ),
                'zip': ("billingInfo_zipCode" in contactfields and contactfields["billingInfo_zipCode"]),
                'phone': self.full_phone( contactfields ),
                'producteca_bindings': [(6, 0, [client.id])],
                'email': (client and client.mail) or '',
                #'meli_buyer_id': Buyer['id']
            }
            if "company_ids" in self.env["res.partner"]._fields and company:
                ocapi_buyer_fields["company_ids"] = [(4,company.id)]

            if company:
                ocapi_buyer_fields["lang"] =  company.partner_id.lang

            if 'property_account_receivable_id' in self.env["res.partner"]._fields:
                ocapi_buyer_fields['property_account_receivable_id'] = (chanbinded and chanbinded.partner_account_receive_id and chanbinded.partner_account_receive_id.id)

            ocapi_buyer_fields.update( self.doc_info( contactfields, doc_undefined=(account.configuration and account.configuration.doc_undefined) ) )
            _logger.info(ocapi_buyer_fields)

            if len(restot):
                _logger.info("Upgrade partner")
                _logger.info(restot)
                for res in restot:
                    _logger.info("Search Partner "+str(res))
                    partner_id_id = res[1]
                    partner_id = self.env["res.partner"].sudo().browse([partner_id_id])
                    try:

                        if "main_id_number" in partner_id._fields and partner_id.main_id_number and "main_id_number" in ocapi_buyer_fields:
                            del ocapi_buyer_fields["main_id_number"]

                        if "afip_responsability_type_id" in partner_id._fields and partner_id.afip_responsability_type_id and "afip_responsability_type_id" in ocapi_buyer_fields:
                            del ocapi_buyer_fields["afip_responsability_type_id"]

                        if "main_id_category_id" in partner_id._fields and partner_id.main_id_category_id and "main_id_category_id" in ocapi_buyer_fields:
                            del ocapi_buyer_fields["main_id_category_id"]

                        _logger.info("Upgrade partner: "+str(ocapi_buyer_fields))
                        partner_id.sudo().write(ocapi_buyer_fields)
                    except Exception as E:
                        error = {"error": "Updated res.partner error. Check account configuration and this message: "+str(E)}
                        result.append(error)
                        _logger.error(E, exc_info=True)
                    break;
            else:
                _logger.info("Create partner")
                respartner_obj = self.env['res.partner']
                try:
                    partner_id = respartner_obj.sudo().create(ocapi_buyer_fields)
                    if partner_id:
                        _logger.info("Created Res Partner "+str(partner_id))
                except Exception as E:
                    error = {"error": "Created res.partner issue: "+str(E)}
                    result.append(error)
                    _logger.error(str(error["error"]))
                    _logger.error(E, exc_info=True)
                    pass;

        if partner_id:

            if client:
                client.write( { "partner_id": partner_id.id } )

            if (chanbinded and "partner_account_receive_id" in chanbinded._fields and chanbinded.partner_account_receive_id):
                partner_id.sudo().write({"property_account_receivable_id": chanbinded.partner_account_receive_id.id })

            #"docType": "RFC",
            #"docNumber": "24827151",
            #Check billingInfo
            partner_shipping_id = partner_id
            pdelivery_fields = {
                "type": "delivery",
                "parent_id": partner_id.id,
                'name': contactfields['contactPerson'],
                'street': self.street(contact=contactfields),
                'street2': str("location_neighborhood" in contactfields and contactfields["location_neighborhood"]),
                'city': self.city(contact=contactfields),
                'country_id': country_id,
                'state_id': self.ostate( country=country_id, contact=contactfields ),
                'zip': ("location_zipCode"in contactfields and contactfields["location_zipCode"]),
                "comment": ("location_addressNotes" in contactfields and contactfields["location_addressNotes"]) or "",
                "email": (client and client.mail),
                "phone": (client and client.phoneNumber)
                #'producteca_bindings': [(6, 0, [client.id])]
                #'phone': self.full_phone( contactfields,billing=True ),
                #'email':contactfields['billingInfo_email'],
                #'producteca_bindings': [(6, 0, [client.id])]
            }
            if "company_ids" in self.env["res.partner"]._fields and company:
                pdelivery_fields["company_ids"] = [(4,company.id)]
            if company:
                pdelivery_fields["lang"] =  company.partner_id.lang
            #TODO: agregar un campo para diferencia cada delivery res partner al shipment y orden asociado, crear un binding usando values diferentes... y listo
            deliv_id = self.env["res.partner"].sudo().search([("parent_id","=",pdelivery_fields['parent_id']),
                                                        ("type","=","delivery"),
                                                        ('street','=',pdelivery_fields['street'])],
                                                        limit=1)
            if not deliv_id or len(deliv_id)==0:
                _logger.info("Create partner delivery")
                respartner_obj = self.env['res.partner']
                try:
                    deliv_id = respartner_obj.create(pdelivery_fields)
                    if deliv_id:
                        _logger.info("Created Res Partner Delivery "+str(deliv_id))
                        partner_shipping_id = deliv_id
                except Exception as E:
                    error = {"error": "Creating partner error. Check account configuration and this message: "+str(E)}
                    result.append(error)
                    _logger.error(str(error["error"]))
                    _logger.error(E, exc_info=True)
                    pass;
            else:
                try:
                    deliv_id.write(pdelivery_fields)
                    partner_shipping_id = deliv_id
                except Exception as E:
                    error = {"error": "Updating partner error. Check account configuration and this message: "+str(E)}
                    result.append(error)
                    _logger.error(str(error["error"]))
                    _logger.error(E, exc_info=True)
                    pass;

            #USING SEQUENCE
            #if 'company_id' in vals:
            #    sale_order_fields['name'] = self.env['ir.sequence'].with_context(force_company=company).next_by_code('sale.order') or _('New')
            #else:
            #    vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')

            plist = None
            #
            if not plist and account.configuration and account.configuration.import_price_lists:
                _logger.info(account.configuration.import_price_lists)
                plist = account.configuration.import_price_lists[0]

            if not plist and account.configuration and account.configuration.publish_price_lists:
                _logger.info(account.configuration.publish_price_lists)
                plist = account.configuration.publish_price_lists[0]

            if not plist:
                plist = self.env["product.pricelist"].search([],limit=1)

            whouse = None
            #import_sales_action
            if account.configuration and account.configuration.import_stock_locations:

                _logger.info(account.configuration.import_stock_locations)
                #default is first instance
                whouse = chanbinded and chanbinded.warehouse_id or account.configuration.import_stock_locations[0]
                #account.configuration.import_stock_locations

                #check for logistic type
                if pso.logisticType:
                    _logger.info( "account.configuration.import_stock_locations:" + str(account.configuration.import_stock_locations.mapped("id")) )
                    whousefull = self.env["stock.warehouse"].search([('producteca_logistic_type','=',str(pso.logisticType))])
                    if len(whousefull):
                        for wh in whousefull:
                            if wh.id in account.configuration.import_stock_locations.mapped("id"):
                                whouse = wh
                                break;

            sale_order_fields = {
                #TODO: "add parameter for":
                'name': fields['name'],
                'partner_id': partner_id.id,
                'partner_shipping_id': partner_shipping_id.id,
                'pricelist_id': (plist and plist.id),
                'warehouse_id': (whouse and whouse.id),
                'company_id': (company and company.id)
            }
            seller_user = (chanbinded and "seller_user" in chanbinded._fields and chanbinded.seller_user) or (account and account.configuration and account.configuration.seller_user)
            seller_team = (chanbinded and "seller_team" in chanbinded._fields and chanbinded.seller_team) or (account and account.configuration and account.configuration.seller_team)
            if (seller_user):
                sale_order_fields["user_id"] = seller_user.id
            if (seller_team):
                sale_order_fields["team_id"] = seller_team.id

            if (1==1 and "x_studio_referencia" in self.env["sale.order"]._fields): #VIVALMO
                sale_order_fields["x_studio_referencia"] = fields['name']
                sale_order_fields["client_order_ref"] = fields['name']
                sale_order_fields["analytic_account_id"] = chanbinded.analytic_account_id and chanbinded.analytic_account_id.id

            if chan:
                sale_order_fields['name'] = fields['name']

            if not so:
                so = self.env["sale.order"].search([('name','like',sale_order_fields['name'])],limit=1)

            if so:
                _logger.info("Updating order")
                _logger.info(sale_order_fields)
                so.write(sale_order_fields)
            else:
                _logger.info("Creating order")
                _logger.info(sale_order_fields)
                so = self.env["sale.order"].create(sale_order_fields)

            if so and 1==1 and "x_studio_referencia" in self.env["sale.order"]._fields:
                so.commitment_date = so.date_order

        #process "lines"
        if "lines" in sale and pso:
            lines = sale["lines"]
            for line in lines:
                lid = str(psoid)+str("_")+str(line["variation"]["id"])
                linefields = {
                    "conn_id": lid,
                    "connection_account": account.id,
                    "order_id": pso.id,
                    "name": str(line["product"]["name"])+" ["+str(line["variation"]["sku"])+"]"
                }
                lineskey_bind = ["price",
                    "originalPrice",
                    "product",
                    "variation",
                    "quantity",
                    "conversation",
                    "reserved"]
                model = self.env["producteca.sale_order_line"]
                for k in lineskey_bind:
                    key = k
                    if key in line:
                        val = line[key]
                        fieldname = key
                        if type(val)==dict:
                            for skey in val:
                                fieldname = key+"_"+skey
                                if not fieldname in model._fields:
                                    continue;

                                if type(val[skey])==dict:
                                    linefields[key+"_"+skey] = str(val[skey])
                                else:
                                    linefields[key+"_"+skey] = val[skey]
                        else:
                            if not fieldname in model._fields:
                                continue;
                            linefields[key] = val

                _logger.info(linefields)
                _logger.info("Searching Producteca Line: " + str(lid))
                oli = self.env["producteca.sale_order_line"].sudo().search([( 'conn_id', '=', lid ),
                                                                    ('order_id','=',pso.id),
                                                                    ("connection_account","=",account.id)])
                if not oli:
                    _logger.info("Creating producteca order line")
                    oli = self.env["producteca.sale_order_line"].sudo().create( linefields )
                else:
                    _logger.info("Updating producteca order line")
                    oli.write( linefields )
                if not oli:
                    error = {"error": "Producteca Order Line creation error"}
                    #errors+= str(error)+"\n"
                    result.append(error)
                    if so:
                        so.message_post(body=str(error["error"]))
                    return result
                else:
                    _logger.info("Line ok")
                    _logger.info(oli)

                product = self.env["product.product"].search( [('default_code','=',line["variation"]["sku"])] )
                _logger.info("product searched = sku ["+str(line["variation"]["sku"])+"]: "+str(product))
                #product = self.env["product.product"].search( [('barcode','=',line["variation"]["sku"])] )
                if not product:
                    product = self.env["product.product"].search( [('default_code','like',line["variation"]["sku"])] )
                    _logger.info("product searched like sku ["+str(line["variation"]["sku"])+"]: "+str(product))

                if not product:
                    product = self.env["product.product"].search( [('barcode','like',line["variation"]["sku"])] )

                if product and len(product)>1:
                    error = { "error":  "Duplicados del producto con sku (revisar sku/barcode) "+str(line["variation"]["sku"]) }
                    result.append(error)
                    if so:
                        so.message_post(body=str(error["error"]))

                if not product:
                    error = { "error":  "Error no se encontro el producto "+str(line["variation"]["sku"]) }
                    #errors+= str(error)+"\n"
                    result.append(error)
                    #return result
                    if so:
                        so.message_post(body=str(error["error"]))
                else:
                    #create order line item
                    if so and product and len(product)==1:
                        soline_mod = self.env["sale.order.line"]
                        so_line_fields = {
                            'company_id': company.id,
                            'order_id': so.id,
                            #'meli_order_item_id': Item['item']['id'],
                            #'meli_order_item_variation_id': Item['item']['variation_id'],
                            'price_unit': self.ocapi_price_unit( product, float(linefields['price']) ),
                            'product_id': product.id,
                            'product_uom_qty': float(linefields['quantity']),
                            'product_uom': product.uom_id.id,
                            'name': product.display_name or linefields['name'],
                        }
                        _logger.info("Creating Odoo Sale Order Line Item: "+str(so_line_fields))
                        so_line = soline_mod.search( [  #('meli_order_item_id','=',saleorderline_item_fields['meli_order_item_id']),
                                                        #('meli_order_item_variation_id','=',saleorderline_item_fields['meli_order_item_variation_id']),
                                                        ('product_id','=',product.id),
                                                        ('order_id','=',so.id)] )

                        if not so_line or len(so_line)==0:
                            so_line = soline_mod.create( ( so_line_fields ))
                        else:
                            so_line.write( ( so_line_fields ) )

                        if so_line and oli:
                            #Many2one this time
                            so_line.producteca_bindings = oli

                        product.product_tmpl_id.producteca_bind_to(account)
                        #product.producteca_bind_to(account)

        #process "shipments", create res.partner shipment services
        if "shipments" in sale and pso:
            shipments = sale["shipments"]

            for shipment in shipments:
                shpid = str(psoid)+str("_")+str(shipment["id"])
                shpfields = {
                    "conn_id": shpid,
                    "connection_account": account.id,
                    "order_id": pso.id,
                    "name": "SHP "+str(shipment["id"])
                }
                shpkey_bind = ["date",
                    "method",
                    "integration",
                    "receiver"]
                model = self.env["producteca.shipment"]
                for k in shpkey_bind:
                    key = k
                    if key in shipment:
                        val = shipment[key]
                        fieldname = key
                        if type(val)==dict:
                            for skey in val:
                                fieldname = key+"_"+skey
                                if not fieldname in model._fields:
                                    continue;
                                if type(val[skey])==dict:
                                    shpfields[key+"_"+skey] = str(val[skey])
                                else:
                                    shpfields[key+"_"+skey] = val[skey]
                        else:
                            if not fieldname in model._fields:
                                continue;
                            if key =="date":
                                val = ml_datetime(val)
                            shpfields[key] = val

                _logger.info(shpfields)
                _logger.info("Searching Producteca Shipment: " + str(shpid))
                oshp = self.env["producteca.shipment"].sudo().search([( 'conn_id', '=', shpid ),
                                                                    ('order_id','=',pso.id),
                                                                    ("connection_account","=",account.id)])
                if not oshp:
                    _logger.info("Creating producteca shipment record")
                    oshp = self.env["producteca.shipment"].sudo().create( shpfields )
                else:
                    _logger.info("Updating producteca shipment record")
                    oshp.write( shpfields )
                if not oshp:
                    error = {"error": "Producteca Order Shipment creation error"}
                    result.append(error)
                    if so:
                        so.message_post(body=str(error["error"]))
                    return result
                else:
                    _logger.info("Shipment ok")
                    _logger.info(oshp)


                #CREATING SHIPMENT SERVICE AND CARRIERS

                product_obj = self.env["product.product"]
                product_tpl = self.env["product.template"]
                ship_name = oshp.method_courier or (oshp.method_mode=="custom" and "Personalizado")

                if not ship_name or len(ship_name)==0:
                    continue;

                product_shipping_id = product_obj.search(['|','|',('default_code','=','ENVIO'),
                            ('default_code','=',ship_name),
                            ('name','=',ship_name)] )

                if len(product_shipping_id):
                    product_shipping_id = product_shipping_id[0]
                else:
                    product_shipping_id = None
                    ship_prod = {
                        "name": ship_name,
                        "default_code": ship_name,
                        "type": "service",
                        #"taxes_id": None
                        #"categ_id": 279,
                        #"company_id": company.id
                    }
                    _logger.info(ship_prod)
                    product_shipping_tpl = product_tpl.create((ship_prod))
                    if (product_shipping_tpl):
                        product_shipping_id = product_shipping_tpl.product_variant_ids[0]
                _logger.info(product_shipping_id)

                if (not product_shipping_id):
                    _logger.info('Failed to create shipping product service')
                    continue;

                ship_carrier = {
                    "name": ship_name,
                }
                ship_carrier["product_id"] = product_shipping_id.id
                ship_carrier_id = self.env["delivery.carrier"].search([ ('name','=',ship_carrier['name']) ])
                if not ship_carrier_id:
                    ship_carrier_id = self.env["delivery.carrier"].create(ship_carrier)
                if (len(ship_carrier_id)>1):
                    ship_carrier_id = ship_carrier_id[0]

                if not so:
                    continue;
                stock_pickings = self.env["stock.picking"].search([('sale_id','=',so.id),('name','like','OUT')])
                #carrier_id = self.env["delivery.carrier"].search([('name','=',)])
                for st_pick in stock_pickings:
                    #if ( 1==2 and ship_carrier_id ):
                    #    st_pick.carrier_id = ship_carrier_id
                    st_pick.carrier_tracking_ref = oshp.method_trackingNumber

                if (oshp.method_courier == "MEL Distribution"):
                    _logger.info('MEL Distribution, not adding to order')
                    #continue

                #if ( ship_carrier_id and not so.carrier_id and pso.shippingCost and pso.shippingCost>0.0 ):
                if ( ship_carrier_id and not so.carrier_id  ):
                    so.carrier_id = ship_carrier_id
                    #vals = sorder.carrier_id.rate_shipment(sorder)
                    #if vals.get('success'):
                    #delivery_message = vals.get('warning_message', False)
                    delivery_message = "Defined by Producteca"
                    #delivery_price = vals['price']
                    delivery_price = self.ocapi_price_unit( product_shipping_id, float(pso.shippingCost) )
                    #display_price = vals['carrier_price']
                    #_logger.info(vals)
                    set_delivery_line( so, delivery_price, delivery_message )

                if ((so.carrier_id and pso.shippingCost==0.0 ) or including_shipping_cost=="never"):
                    delivery_line = get_delivery_line( so )
                    if delivery_line:
                        delivery_line.price_unit = float(0.0)
                        delivery_line.qty_to_invoice = 0.0
                #    so._remove_delivery_line()

                if so and pso and pso.shipment_method_cost:
                    delivery_line = get_delivery_line( so )
                    if delivery_line and 'purchase_price' in saleorderline_obj._fields:
                        delivery_line.purchase_price = float(pso.shipment_method_cost)

                if ((so.carrier_id and pso.shippingCost==0.0) and including_shipping_cost=="never"):
                    so._remove_delivery_line()


        #process payments
        if "payments" in sale and pso:
            payments = sale["payments"]
            for payment in payments:
                payid = str(psoid)+str("_")+str(payment["id"])
                payfields = {
                    "conn_id": payid,
                    "connection_account": account.id,
                    "order_id": pso.id,
                    "name": "PAY "+str(payment["id"])
                }
                paykey_bind = ["date",
                    "amount",
                    "couponAmount",
                    "status",
                    "method",
                    "integration",
                    "transactionFee",
                    "card",
                    "hasCancelableStatus",
                    "installments"]
                model = self.env["producteca.payment"]
                for k in paykey_bind:
                    key = k
                    fieldname = key
                    if key in payment:
                        val = payment[key]
                        if type(val)==dict:
                            for skey in val:
                                fieldname = key+"_"+skey
                                if not fieldname in model._fields:
                                    continue;
                                if type(val[skey])==dict:
                                    payfields[key+"_"+skey] = str(val[skey])
                                else:
                                    payfields[key+"_"+skey] = val[skey]
                        else:
                            if not fieldname in model._fields:
                                continue;
                            if key =="date":
                                val = ml_datetime(val)
                            payfields[key] = val

                _logger.info(payfields)
                _logger.info("Searching Producteca Payment: " + str(payid))
                opay = self.env["producteca.payment"].sudo().search([( 'conn_id', '=', payid ),
                                                                    ('order_id','=',pso.id),
                                                                    ("connection_account","=",account.id)])
                if not opay:
                    _logger.info("Creating producteca payment record")
                    opay = self.env["producteca.payment"].sudo().create( payfields )
                else:
                    _logger.info("Updating producteca payment record")
                    opay.write( payfields )
                if not opay:
                    error = {"error": "Producteca Order Payment creation error"}
                    result.append(error)
                    if so:
                        so.message_post(body=str(error["error"]))
                    return result
                else:
                    opay.order_id = pso
                    _logger.info("Producteca Payment ok, creating Odoo Payment.")
                    _logger.info(opay)
                    if opay.status and opay.status=='Approved' and account and account.configuration:
                        if (account.configuration.import_payments==True and not opay.account_payment_id):
                            _logger.info("Importing payment...")
                            try:
                                opay.create_payment()
                            except Exception as E:
                                error = {"error": "Creating payment error. Check account configuration and this message: "+str(E)}
                                result.append(error)
                                _logger.error(str(error["error"]))
                                _logger.error(E, exc_info=True)
                                if so:
                                    so.message_post(body=str(error["error"]))
                                pass;
                        elif opay.account_payment_id and "account_payment_group_id" in opay._fields:
                            if not opay.account_payment_group_id:
                                opay.account_payment_group_id = opay.account_payment_id.payment_group_id
                            if opay.account_payment_group_id and not opay.account_payment_group_id.receiptbook_id:
                                opay.account_payment_group_id.receiptbook_id = opay.get_ml_receiptbook()
                            if opay.account_payment_group_id and not opay.account_payment_group_id.partner_type:
                                opay.account_payment_group_id.partner_type = "customer"


                        if (account.configuration.import_payments_fee==True and not opay.account_supplier_payment_id):
                            try:
                                opay.create_supplier_payment()
                            except Exception as E:
                                error = {"error": "Creating payment fee error. Check account configuration and this message: "+str(E)}
                                result.append(error)
                                _logger.error(str(error["error"]))
                                _logger.error(E, exc_info=True)
                                if so:
                                    so.message_post(body=str(error["error"]))
                                pass;
                        if (account.configuration.import_payments_shipment==True and not opay.account_supplier_payment_shipment_id):
                            try:
                                opay.create_supplier_payment_shipment()
                            except Exception as E:
                                error = {"error": "Creating payment shipment error. Check account configuration and this message: "+str(E)}
                                result.append(error)
                                _logger.error(str(error["error"]))
                                _logger.error(E, exc_info=True)
                                if so:
                                    so.message_post(body=str(error["error"]))
                                pass;

                #Register Payments...

            if so:
                _logger.info("Order ok")
                _logger.info(so)
                pso.write({ "sale_order": so.id })
                if so_bind_now:
                    so.producteca_bindings = so_bind_now

                #ADD COMISION
                #product_fee = "product_fee" in chan and config.mercadolibre_product_fee
                product_fee = False
                fea_amount = pso.transaction_fee

                if not product_fee:
                    product_fee = self.env["product.product"].search( ['|','|',('default_code','ilike','COMISION_ML'),('default_code','ilike','COMISIONML'),('default_code','ilike','COMISION ML')], limit=1 )

                if product_fee and 'purchase_price' in saleorderline_obj._fields:

                    com_name = ((product_fee and product_fee.display_name) or "COMISION ")
                    com_name+=  str(" ")+ str(psoid)
                    #if (order_item and order_item.product_id and order_item.product_id.default_code):
                    #    com_name+= str(" ") + str(order_item.product_id.default_code)

                    saleorderline_item_fields = {
                        'company_id': company.id,
                        'order_id': so.id,
                        #'producteca_order_id': meli_order_item_id,
                        #'meli_order_item_variation_id': meli_order_item_variation_id,
                        'purchase_price': float(fea_amount),
                        'price_unit': float(0.0),
                        'product_id': (product_fee and product_fee.id),
                        'product_uom_qty': 1.0,
                        'product_uom': (product_fee and product_fee.uom_id.id),
                        'name': com_name,
                    }
                    #saleorderline_item_fields.update( self._set_product_unit_price( product_related_obj=product_related_obj, Item=Item, config=config ) )

                    saleorderline_item_ids = saleorderline_obj.search( [
                                                                        #('meli_order_item_id','=',meli_order_item_id),
                                                                        #('meli_order_item_variation_id','=',meli_order_item_variation_id),
                                                                        ('product_id','=',product_fee.id),
                                                                        ('order_id','=',so.id)], limit=1 )

                    if not saleorderline_item_ids:
                        saleorderline_item_ids = saleorderline_obj.create( ( saleorderline_item_fields ))
                    else:
                        saleorderline_item_ids.write( ( saleorderline_item_fields ) )


        #try:
        if so:
            import_sales_action = False
            import_sales_action = chanbinded and chanbinded.import_sales_action
            full_log = chanbinded and chanbinded.import_sales_action_full_logistic

            import_sales_action = import_sales_action or account.configuration.import_sales_action
            full_log = full_log or account.configuration.import_sales_action_full_logistic
            if full_log:
                if full_log in str(pso.logisticType):
                    import_sales_action = chanbinded and chanbinded.import_sales_action_full
                    import_sales_action = import_sales_action or account.configuration.import_sales_action_full


            if import_sales_action and so.producteca_bindings:

                #update state:
                pso.state = "payment_required"
                if pso.isOpen:
                    pso.state = "confirmed"
                if pso.paymentStatus in ['Approved']:
                    pso.state = "paid"
                if pso.paymentStatus in ['InMediation']:
                    pso.state = "payment_in_process"
                if pso.paymentStatus in ['Refunded']:
                    pso.state = "refunded"
                if pso.isCanceled:
                    pso.state = "cancelled"
                #if so.producteca_bindings[0].isOpen:
                #    pso.state = "confirmed"

                #check action:
                cond_total = abs(so.amount_total - so.producteca_bindings[0].paidApproved ) <= 1.0

                if (including_shipping_cost=="never"):
                    cond_total = abs(so.amount_total - so.producteca_bindings[0].amount_no_shipping ) <= 1.0

                cond = cond_total and so.producteca_bindings[0].paymentStatus in ['Approved']
                cond_refunded = so.producteca_bindings[0].paymentStatus in ['Refunded']
                cond_canceled = so.producteca_bindings[0].isCanceled

                _logger.info("import_sales_action: "+str(import_sales_action)+" cond:"+str(cond))
                _logger.info("so.name: "+str(so.name)+" so.state: "+str(so.state))
                _logger.info("cond_refunded: "+str(cond_refunded)+" paymentStatus: "+str(so.producteca_bindings[0].paymentStatus))
                _logger.info("cond_canceled: "+str(cond_canceled)+"  isCanceled: "+str(so.producteca_bindings[0].isCanceled))

                if "payed_confirm_order" in import_sales_action:
                    if so.state in ['draft','sent'] and cond:
                        so.action_confirm()
                    if so.state in['open','done','sale'] and cond_refunded:
                        if cond_canceled:
                            _logger.info("Cancelling order")
                            so.action_cancel()

                if "_shipment" in import_sales_action:
                    if so.state in ['sale','done']:
                        _logger.info("Shipment confirm")
                        dones = False
                        cancels = False
                        drafts = False
                        if cond:
                            if so.picking_ids:
                                for spick in so.picking_ids:
                                    _logger.info(str(spick)+" state:"+str(spick.state))
                                    if spick.state in ['done']:
                                        dones = True
                                    elif spick.state in ['cancel']:
                                        cancels = True
                                    else:
                                        drafts = True
                            else:
                                dones = False

                            if drafts:
                                #drafts then nothing is full done
                                dones = False

                            if dones:
                                _logger.info("Shipment complete")
                            else:
                                _logger.info("Shipment not complete: TODO: make an action, dones:"+str(dones)+" drafts: "+str(drafts)+" cancels:"+str(cancels))
                                so.producteca_deliver()

                if "_invoice" in import_sales_action:
                    if so.state in ['sale','done']:
                        _logger.info("Invoice confirm")
                        dones = False
                        cancels = False
                        drafts = False
                        if cond:
                            if so.picking_ids:
                                for spick in so.picking_ids:
                                    _logger.info(str(spick)+" state:"+str(spick.state))
                                    if spick.state in ['done']:
                                        dones = True
                                    elif spick.state in ['cancel']:
                                        cancels = True
                                    else:
                                        drafts = True
                            else:
                                dones = False

                            if drafts:
                                #drafts then nothing is full done
                                dones = False

                            if dones:
                                _logger.info("Creating invoice...")
                                #invoices = self.env[acc_inv_model].search([('invoice_origin','=',so.name)])
                                invoices = so.invoice_ids

                                if not invoices:
                                    _logger.info("Creating new invoices")
                                    res = so.action_invoice_create(grouped=True) #agrupar por SO id
                                    _logger.info("invoice create res:"+str(res))
                                    #invoices = self.env[acc_inv_model].search([('invoice_origin','=',so.name)])

                                if invoices:
                                    for inv in invoices:
                                        #try:
                                        _logger.info("Invoice to process:"+str( inv.name ) )
                                        if inv.state in ['draft']:
                                            if (chanbinded and chanbinded.journal_id):
                                                #chanbinded and chanbinded.journal_id and inv.write({"journal_id": chanbinded.journal_id.id })
                                                if ('account.journal.document.type' in  self.env and
                                                    'journal_document_type_id' in inv._fields
                                                    and inv.journal_document_type_id
                                                    and inv.journal_document_type_id.document_type_id
                                                    and not (inv.journal_document_type_id.journal_id.id==chanbinded.journal_id.id)):

                                                    doctype = self.env['account.journal.document.type'].search([('document_type_id','=',inv.journal_document_type_id.document_type_id.id),('journal_id','=',chanbinded.journal_id.id)],limit=1)
                                                    if doctype:
                                                        #inv.journal_document_type_id = doctype.id
                                                        inv.write({"journal_id": chanbinded.journal_id.id, "journal_document_type_id": doctype.id  })

                                                inv.write({"journal_id": chanbinded.journal_id.id, "account_id": (chanbinded and chanbinded.partner_account_receive_id and chanbinded.partner_account_receive_id.id) })

                                            _logger.info("Validate invoice: "+str(inv.name)+" journal:"+str(inv.journal_id and inv.journal_id.name))
                                            _logger.info("main_id_number: "+str(inv.partner_id.main_id_number))
                                            if inv.partner_id and inv.partner_id.main_id_number and inv.partner_id.afip_responsability_type_id and inv.partner_id.main_id_category_id:
                                                inv.action_invoice_open()
                                            else:
                                                error = { 'error': 'Datos de facturación incompletos, revisar Responsabilidad, Tipo de documento y número.' }
                                                _logger.error(str(error["error"]))
                                                #_logger.error(E, exc_info=True)
                                                if so:
                                                    so.message_post(body=str(error["error"]))
                                        if inv.state in ['open'] and not inv.producteca_inv_attachment_id:
                                            _logger.info("Send to Producteca: "+str(inv.name))
                                            inv.enviar_factura_producteca()
                                        elif inv.state in ['open']:
                                            _logger.info("Invoice already sent: result:"+str(result))
                                        #except:
                                            #inv.message_post()
                                        #    error = {"error": "Invoice Error"}
                                        #    result.append(error)
                                        #    raise;
                            else:
                                _logger.info("Creating invoices not processed, shipment not complete: dones:"+str(False)+" drafts: "+str(drafts)+" cancels:"+str(cancels))
                        else:
                            _logger.error("Conditions not met for invoicing > cond_total: " + str(cond_total) +" cond: "+str(cond) )
        #except Exception as E:
        #    error = {"error": "Error sale order post processing error: " +str(E)}
        #    _logger.error(error)
        #    result.append(error)
        #    pass;

        if noti:
            errors = str(result)
            #logs = str(sale)
            noti.stop_internal_notification(errors=errors,logs=noti.processing_logs)

        return result

    def import_products( self ):
        #

        return ""

    def import_product( self ):
        #

        return ""

    def import_image( self ):
        #

        return ""

    def import_shipment( self ):
        #

        return ""

    def import_payment( self ):
        #

        return ""
