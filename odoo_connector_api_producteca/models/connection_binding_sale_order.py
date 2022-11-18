# -*- coding: utf-8 -*-

from odoo import fields, osv, models, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
import pdb
#from .warning import warning
import requests

from .versions import *
from odoo.exceptions import UserError, ValidationError


class OcapiConnectionBindingSaleOrderPayment(models.Model):

    _name = "producteca.payment"
    _description = "Producteca Sale Order Payment Binding"
    _inherit = "ocapi.binding.payment"

    order_id = fields.Many2one("producteca.sale_order",string="Order")
    payment_id = fields.Char( related="conn_id", string="Payment Id", index=True )
    channel_binding_id = fields.Many2one( "producteca.channel.binding",related="order_id.channel_binding_id",string="Channel Binding")
    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )
    name = fields.Char(string="Payment Name", index=True)

    date = fields.Datetime(string="date",index=True)
    amount = fields.Float(string="amount")
    couponAmount = fields.Float(string="couponAmount")
    status = fields.Char(string="status",index=True)
    method = fields.Char(string="method",index=True)
    integration_integrationId = fields.Char(string="integrationId",index=True)
    integration_app = fields.Char(string="app")
    transactionFee = fields.Float(string="transactionFee")
    installments = fields.Char(string="installments")
    card_paymentNetwork = fields.Char(string="card paymentNetwork")
    card_firstSixDigits = fields.Char(string="card firstSixDigits")
    card_lastFourDigits = fields.Char(string="card lastFourDigits")
    hasCancelableStatus = fields.Char(string="hasCancelableStatus")

    account_payment_id = fields.Many2one('account.payment',string='Pago')
    account_supplier_payment_id = fields.Many2one('account.payment',string='Pago a Proveedor')
    account_supplier_payment_shipment_id = fields.Many2one('account.payment',string='Pago Envio a Proveedor')

    #account_payment_group_id = fields.Many2one('account.payment.group',string='Pago agrupado')
    #account_supplier_group_payment_id = fields.Many2one('account.payment.group',string='Pago agrupado a Proveedor')
    #account_supplier_group_payment_shipment_id = fields.Many2one('account.payment.group',string='Pago agrupado Envio a Proveedor')

    def get_ml_receiptbook( self ):
        receiptbook_id = self.channel_binding_id and self.channel_binding_id.account_payment_receiptbook_id
        return receiptbook_id

    def _get_ml_receiptbook( self ):
        receiptbook_id = self.channel_binding_id and self.channel_binding_id.account_payment_receiptbook_id
        return receiptbook_id

    def _get_ml_journal(self):
        journal_id = self.channel_binding_id and self.channel_binding_id.payment_journal_id
        return journal_id

    def _get_ml_partner(self):
        partner_id = self.channel_binding_id and self.channel_binding_id.partner_id
        return partner_id

    def _get_ml_customer_partner(self):
        sale_order = self._get_ml_customer_order()
        return (sale_order and sale_order.partner_id)

    def _get_ml_customer_order(self):
        mlorder = self.order_id
        #mlshipment = mlorder.shipment
        return (mlorder and mlorder.sale_order)
        # or (mlshipment and mlshipment.sale_order)

    def create_payment(self):
        _logger.info("create_payment")
        self.ensure_one()
        if self.account_payment_id:
            raise ValidationError('Ya esta creado el pago')

        if self.status != 'Approved':
            raise ValidationError('Not approved')

        journal_id = self._get_ml_journal()
        payment_method_id = self.env['account.payment.method'].search([('code','=','inbound_online_producteca'),('payment_type','=','inbound')])

        if not journal_id or not payment_method_id:
            raise ValidationError('Debe configurar el diario/metodo de pago')

        payment_method_line_id = self.env['account.payment.method.line'].search([('journal_id','=',journal_id.id),
                                                                                ('payment_method_id','=',payment_method_id.id),
                                                                                ('payment_type','=','inbound')])

        if not payment_method_line_id:
            raise ValidationError('Debe configurar el diario/metodo de pago con el metodo de pago')

        partner_id = self._get_ml_customer_partner()
        if not partner_id:
            raise ValidationError('No se pudo establecer el partner del pago')
        #currency_id = self.env['res.currency'].search([('name','=',self.currency_id)])
        currency_id = self.connection_account.company_id.currency_id

        if not currency_id:
            raise ValidationError('No se puede encontrar la moneda del pago')

        communication = self.payment_id
        if self._get_ml_customer_order():
            communication = ""+str(self._get_ml_customer_order().name)+" OP "+str(self.payment_id)+str(" TOT")

        vals_payment = {
                #'account_id': journal_id.default_debit_account_id.id,
                'partner_id': partner_id.id,
                'payment_type': 'inbound',
                'payment_method_id': payment_method_id.id,
                'payment_method_line_id': payment_method_line_id.id,
                'journal_id': journal_id.id,
                #'meli_payment_id': self.id,
                'currency_id': currency_id.id,
                'partner_type': 'customer',
                'amount': self.amount,
                }
        vals_payment[acc_pay_ref] = communication
        acct_payment_id = None
        if 'account.payment.group' in self.env:
            vals_group = {
                'company_id': self.connection_account.company_id.id,
                'receiptbook_id': (self._get_ml_receiptbook() and self._get_ml_receiptbook().id),
                'partner_id': partner_id.id,
                #'journal_id': journal_id.id,
                'currency_id': currency_id.id,
                'partner_type': 'customer',
                'payment_ids': [(0,0,vals_payment)]
            }
            vals_group[acc_pay_ref] = communication
            _logger.info("create_payment group: "+str(vals_group))
            acct_payment_group_id = self.env['account.payment.group'].create( vals_group )
            if acct_payment_group_id:
                acct_payment_id = acct_payment_group_id.payment_ids and acct_payment_group_id.payment_ids[0].id
                self.account_payment_id = acct_payment_id
                self.account_payment_group_id = acct_payment_group_id.id
                if self.channel_binding_id and ("account_payment_receipt_validation" in self.channel_binding_id._fields) and self.channel_binding_id.account_payment_receipt_validation:
                    if self.channel_binding_id.account_payment_receipt_validation in ['validate']:
                        payment_post( acct_payment_group_id )

        else:
            _logger.info("create_payment default: "+str(vals_payment))
            acct_payment_id = self.env['account.payment'].create(vals_payment)
            self.account_payment_id = (acct_payment_id and acct_payment_id.id)
            if self.channel_binding_id and ("account_payment_receipt_validation" in self.channel_binding_id._fields) and self.channel_binding_id.account_payment_receipt_validation:
                if self.channel_binding_id.account_payment_receipt_validation in ['validate']:
                    payment_post( acct_payment_id )
            #payment_post( acct_payment_id )



    def create_supplier_payment(self):
        self.ensure_one()

        if self.status != 'Approved':
            raise ValidationError('Not approved')

        if self.account_supplier_payment_id:
            raise ValidationError('Ya esta creado el pago')

        journal_id = self._get_ml_journal()
        payment_method_id = self.env['account.payment.method'].search([('code','=','outbound_online_producteca'),('payment_type','=','outbound')])

        if not journal_id or not payment_method_id:
            raise ValidationError('Debe configurar el diario/metodo de pago')

        payment_method_line_id = self.env['account.payment.method.line'].search([('journal_id','=',journal_id.id),
                                                                                ('payment_method_id','=',payment_method_id.id),
                                                                                ('payment_type','=','inbound')])

        if not payment_method_line_id:
            raise ValidationError('Debe configurar el diario/metodo de pago con el metodo de pago')

        partner_id = self._get_ml_partner()
        if not partner_id:
            raise ValidationError('No esta dado de alta el proveedor MercadoLibre')

        currency_id = self.connection_account.company_id.currency_id
        if not currency_id:
            raise ValidationError('No se puede encontrar la moneda del pago')

        communication = self.payment_id
        if self._get_ml_customer_order():
            communication = ""+str(self._get_ml_customer_order().name)+" OP "+str(self.payment_id)+str(" FEE")

        vals_payment = {
                #'account_id': journal_id.default_debit_account_id.id,
                'partner_id': partner_id.id,
                'payment_type': 'outbound',
                'payment_method_id': payment_method_id.id,
                'payment_method_line_id': payment_method_line_id.id,
                'journal_id': journal_id.id,
                #'meli_payment_id': self.id,
                'currency_id': currency_id.id,
                'partner_type': 'supplier',
                'amount': self.transactionFee,
                }
        vals_payment[acc_pay_ref] = communication
        acct_payment_id = self.env['account.payment'].create(vals_payment)

        if 'account.payment.group' in self.env:
            vals_group = {
                'company_id': self.connection_account.company_id.id,
                'receiptbook_id': (self._get_ml_receiptbook() and self._get_ml_receiptbook().id),
                'partner_id': partner_id.id,
                #'journal_id': journal_id.id,
                'currency_id': currency_id.id,
                'partner_type': 'supplier',
                'payment_ids': [(0,0,vals_payment)]
            }
            vals_group[acc_pay_ref] = communication
            _logger.info("create_supplier_payment group: "+str(vals_group))
            acct_payment_group_id = self.env['account.payment.group'].create( vals_group )
            if acct_payment_group_id:
                acct_payment_id = acct_payment_group_id.payment_ids and acct_payment_group_id.payment_ids[0].id
                self.account_supplier_payment_id = acct_payment_id
                self.account_supplier_group_payment_id = acct_payment_group_id.id
                if self.channel_binding_id and ("account_payment_receipt_validation" in self.channel_binding_id._fields) and self.channel_binding_id.account_payment_receipt_validation:
                    if self.channel_binding_id.account_payment_receipt_validation in ['validate']:
                        payment_post( acct_payment_group_id )

        else:
            _logger.info("create_supplier_payment default: "+str(vals_payment))
            acct_payment_id = self.env['account.payment'].create(vals_payment)
            self.account_supplier_payment_id = (acct_payment_id and acct_payment_id.id)
            if self.channel_binding_id and ("account_payment_receipt_validation" in self.channel_binding_id._fields) and self.channel_binding_id.account_payment_receipt_validation:
                if self.channel_binding_id.account_payment_receipt_validation in ['validate']:
                    payment_post( acct_payment_id )

    def create_supplier_payment_shipment(self):
        self.ensure_one()
        return None
        if self.status != 'approved':
            return None
        if self.account_supplier_payment_shipment_id:
            raise ValidationError('Ya esta creado el pago')
        journal_id = self._get_ml_journal()
        payment_method_id = self.env['account.payment.method'].search([('code','=','outbound_online_producteca'),('payment_type','=','outbound')])
        if not journal_id or not payment_method_id:
            raise ValidationError('Debe configurar el diario/metodo de pago')
        partner_id = self._get_ml_partner()
        if not partner_id:
            raise ValidationError('No esta dado de alta el proveedor MercadoLibre')

        currency_id = self.connection_account.company_id.currency_id
        if not currency_id:
            raise ValidationError('No se puede encontrar la moneda del pago')

        if (not self.order_id or not self.order_id.financialCost>0.0):
            raise ValidationError('No hay datos de costo de envio')

        communication = self.payment_id
        if self._get_ml_customer_order():
            communication = ""+str(self._get_ml_customer_order().name)+" OP "+str(self.payment_id)+str(" SHP")

        vals_payment = {
                #'account_id': journal_id.default_debit_account_id.id,
                'partner_id': partner_id.id,
                'payment_type': 'outbound',
                'payment_method_id': payment_method_id.id,
                'journal_id': journal_id.id,
                #'meli_payment_id': self.id,
                'currency_id': currency_id.id,
                'partner_type': 'supplier',
                'amount': self.order_id.financialCost,
                }
        vals_payment[acc_pay_ref] = communication
        acct_payment_id = self.env['account.payment'].create(vals_payment)
        self.account_supplier_payment_shipment_id = acct_payment_id and acct_payment_id.id
        if self.channel_binding_id and ("account_payment_receipt_validation" in self.channel_binding_id._fields) and self.channel_binding_id.account_payment_receipt_validation:
            if self.channel_binding_id.account_payment_receipt_validation in ['validate']:
                payment_post( acct_payment_id )



class OcapiConnectionBindingSaleOrderShipmentItem(models.Model):

    _name = "producteca.shipment.item"
    _description = "Ocapi Sale Order Shipment Item"
    _inherit = "ocapi.binding.shipment.item"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )
    shipping_id = fields.Many2one("producteca.shipment",string="Shipment")
    product = fields.Char(string="Product Id")
    variation = fields.Char(string="Variation Id")
    quantity = fields.Float(string="Quantity")


class OcapiConnectionBindingSaleOrderShipment(models.Model):

    _name = "producteca.shipment"
    _description = "Ocapi Sale Order Shipment Binding"
    _inherit = "ocapi.binding.shipment"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )

    order_id = fields.Many2one("producteca.sale_order",string="Order")
    products = fields.One2many("producteca.shipment.item", "shipping_id", string="Product Items")

    date = fields.Datetime(string="date",index=True)
    method_trackingNumber = fields.Char(string="trackingNumber")
    method_trackingUrl = fields.Char(string="trackingUrl")
    method_labelUrl = fields.Char(string="labelUrl")
    method_courier = fields.Char(string="courier")
    method_mode = fields.Char(string="mode")
    method_cost = fields.Char(string="cost")
    method_eta = fields.Char(string="eta")
    method_status = fields.Char(string="method status")
    integration_app = fields.Char(string="app")
    integration_integrationId = fields.Char(string="integrationId")
    integration_status = fields.Char(string="integration status")
    integration_id = fields.Char(string="id")
    receiver_fullName = fields.Char(string="receiver_fullName")
    receiver_phoneNumber = fields.Char(string="receiver_phoneNumber")


class ProductecaConnectionBindingSaleOrderClient(models.Model):

    _name = "producteca.client"
    _description = "Producteca Client Binding"
    _inherit = "ocapi.binding.client"

    def get_display_name(self):
        for client in self:
            client.display_name = str(client.contactPerson)+" ["+str(client.name)+"]"

    display_name = fields.Char(string="Display Name",store=False,compute=get_display_name)
    type = fields.Char(string="Client Type") #Customer, ...
    contactPerson = fields.Char(string="Contact Person")
    mail = fields.Char(string="Mail")
    phoneNumber = fields.Char(string="Phonenumber")
    taxId = fields.Char(string="Tax ID")
    location_streetName = fields.Char(string="Street Name")
    location_streetNumber = fields.Char(string="Street Number")
    location_addressNotes = fields.Char(string="Address Notes")
    location_state = fields.Char(string="State")
    location_stateId = fields.Char(string="State Id")
    location_city = fields.Char(string="City")
    location_neighborhood = fields.Char(string="NeighborHood")
    location_zipCode = fields.Char(string="zipCode")

    profile = fields.Text(string="Profile") # { "app": 2, "integrationId": 63807563 }
    profile_app = fields.Integer(string="Profile App")
    profile_integrationId = fields.Integer(string="Profile Integration Id")

    billingInfo = fields.Text(string="billingInfo")
    billingInfo_docType = fields.Char(string="Doc Type (BI)")
    billingInfo_docNumber = fields.Char(string="Doc Number (BI)")
    billingInfo_streetName = fields.Char(string="Street Name (BI)")
    billingInfo_streetNumber = fields.Char(string="Street Number (BI)")
    billingInfo_zipCode = fields.Char(string="zipCode (BI)")
    billingInfo_city = fields.Char(string="city (BI)")
    billingInfo_state = fields.Char(string="state (BI)")
    billingInfo_stateId = fields.Char(string="state id (BI)")
    billingInfo_neighborhood = fields.Char(string="neighborhood (BI)")
    billingInfo_businessName = fields.Char(string="businessName (BI)")
    billingInfo_stateRegistration = fields.Char(string="stateRegistration (BI)")
    billingInfo_taxPayerType = fields.Char(string="taxPayerType (BI)")
    billingInfo_firstName = fields.Char(string="firstName (BI)")
    billingInfo_lastName = fields.Char(string="lastName (BI)")

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )


class ProductecaConnectionBindingSaleOrderLine(models.Model):

    _name = "producteca.sale_order_line"
    _description = "Producteca Sale Order Line Binding"
    _inherit = "ocapi.binding.sale_order_line"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )
    order_id = fields.Many2one("producteca.sale_order",string="Order")

    price = fields.Float(string="Price")
    originalPrice = fields.Float(string="originalPrice")
    quantity = fields.Float(string="Quantity")
    reserved = fields.Float(string="Reserved")
    conversation = fields.Text(string="Conversation")

    #product
    product_name = fields.Char(string="Product Name")
    product_code = fields.Char(string="Product Code")
    product_brand = fields.Char(string="Product Brand")
    product_id = fields.Char(string="Product Id")
    #variation
    variation_integrationId = fields.Char(string="integrationId")
    variation_maxAvailableStock = fields.Integer(string="maxAvailableStock")
    variation_minAvailableStock = fields.Integer(string="minAvailableStock")
    variation_primaryColor = fields.Char(string="primaryColor")
    variation_size = fields.Char(string="size")
    variation_id = fields.Char(string="Variation Id")
    variation_sku = fields.Char(string="Variation Sku")

    variation_stocks = fields.Text(string="Stocks")
    variation_pictures = fields.Text(string="Pictures")
    variation_attributes = fields.Text(string="Attributes")
    #variation_stocks_warehouse = fields.Char(string="Warehouse")
    #variation_stocks_warehouse = fields.Char(string="Warehouse")

class ProductecaConnectionBindingSaleOrder(models.Model):

    _name = "producteca.sale_order"
    _description = "Producteca Sale Order Binding Sale"
    _inherit = "ocapi.binding.sale_order"

    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )
    client = fields.Many2one("producteca.client",string="Client",index=True)

    lines = fields.One2many("producteca.sale_order_line","order_id", string="Order Items")
    payments = fields.One2many("producteca.payment","order_id",string="Order Payments")
    shipments = fields.One2many("producteca.shipment","order_id",string="Order Shipments")
    sale_notifications = fields.One2many("producteca.notification","producteca_sale_order",string="Notifications")

    def _shipment_method_cost( self ):
        for pord in self:
            pord.shipment_method_cost = 0.0
            if pord.shipments:
                pord.shipment_method_cost = pord.shipments[0].method_cost



    shipment_method_cost = fields.Float(string="Shipment Method Cost",compute=_shipment_method_cost)

    def _transaction_fee( self ):
        for pord in self:
            pord.transaction_fee = 0.0
            if pord.payments:
                tfee = 0.0
                for pp in pord.payments:
                    if pp.status == "Approved":
                        tfee+= pp.transactionFee

                pord.transaction_fee = tfee

    transaction_fee = fields.Float(string="Transaction Fee",compute=_transaction_fee)

    #id connector_id
    status = fields.Selection(related="state",string="Status")

    channel = fields.Char(string="Channel",index=True)
    channel_id = fields.Many2one( "producteca.channel", string="Channel Object")
    channel_binding_id = fields.Many2one( "producteca.channel.binding", string="Channel Binding")
    tags = fields.Char(string="Tags",index=True)
    integrations = fields.Text(string="Integrations",index=True)
    integrations_integrationId = fields.Char(string="integrationId",index=True)
    integrations_app = fields.Char(string="app",index=True)
    integrations_alternateId = fields.Char(string="alternateId")
    cartId = fields.Char(string="cartId",help="Id de carrito (pack_id)")
    warehouse = fields.Text(string="Warehouse",index=True)
    warehouseIntegration = fields.Text(string="WarehouseIntegration",index=True)

    amount = fields.Float(string="Amount",index=True)
    couponAmount = fields.Float(string="couponAmount",index=True)
    def _compute_no_shipping_amount( self ):
        for pso in self:
            pso.amount_no_shipping = pso.amount - pso.shippingCost

    amount_no_shipping = fields.Float(string="Amount No Shipping", compute=_compute_no_shipping_amount, index=True )
    shippingCost = fields.Float(string="Shipping Cost",index=True)
    shippingLink = fields.Char(string="Shipping Link",index=True)
    financialCost = fields.Float(string="Financial Cost",index=True)
    paidApproved = fields.Float(string="Paid Approved",index=True)

    # Approved, InMediation, Refunded
    paymentStatus = fields.Char(string="paymentStatus",index=True)
    #Done, InReturn, InTransit, PickingPending, ReadyToShip, ToBeReturned
    deliveryStatus = fields.Char(string="deliveryStatus",index=True)
    #
    paymentFulfillmentStatus = fields.Char(string="paymentFulfillmentStatus",index=True)

    deliveryFulfillmentStatus = fields.Char(string="deliveryFulfillmentStatus",index=True)
    deliveryMethod = fields.Char(string="deliveryMethod",index=True)
    logisticType = fields.Char(string="logisticType",index=True)
    paymentTerm = fields.Char(string="paymentTerm",index=True)
    currency = fields.Char(string="currency",index=True)
    customId = fields.Char(string="customId",index=True)

    isOpen = fields.Boolean(string="isOpen",index=True)
    isCanceled = fields.Boolean(string="isCanceled",index=True)
    hasAnyShipments = fields.Boolean(string="hasAnyShipments",index=True)

    date = fields.Datetime(string="date",index=True)
    mail = fields.Char(string="Mail")

    #account_payment_group_id = fields.Many2one('account.payment.group',string='Pago agrupado total')

    def get_invoice(self):
        invoice = False
        sale_order = self.sale_order
        invoices = sale_order and sale_order.partner_id and self.env[acc_inv_model].search([('origin','=',sale_order.name)])
        if invoices:
            for inv in invoices:
                if inv.state in ['open']:
                    invoice = inv

        return invoice

    def update(self):
        _logger.info("Update producteca.sale_order")
        #check from last notification
        for pso in self:
            notis = pso and pso.sale_notifications
            if notis:
                _logger.info("producteca_update notis:"+str(notis))
                lastnotix = len(notis)-1
                _logger.info("producteca_update lastnotix:"+str(lastnotix))
                LastNotif = pso.sale_notifications[lastnotix-1]
                _logger.info("producteca_update LastNotif:"+str(LastNotif))
                if LastNotif:
                    if len(self)==1:
                        ret = LastNotif.process_notification()
                        if ret and 'name' in ret:
                            _logger.error(ret)
                            return ret
                    else:
                        try:
                            ret = LastNotif.process_notification()
                        except Exception as e:
                            _logger.error("update pso error: "+str(e))
                            pass;

    def fetch( self, force_update=False ):
        data = {}
        #retreive data from remote database ( Meli: api.mercadolibre.com ; Producteca: last data notification update based on resource value /import_sale/[PR-ID] )
        #Producteca: search last conn_id related to this resource in the notifications

        #MercadoLibre: search last conn_id related to this resource using the REST API (Meli)
        return data

    def refresh( self, data={} ):
        res = {}
        #reprocess the data
        if not (data):
            data = self.fetch()

        #code here...
        #...
        #...

        # # errors:
        # res = { 'error': 'error message' }
        # res = [{ 'error': 'error message' },{ 'error': 'error message 2' },{ 'error': 'error message 3' }]

        # # success:
        # res = True

        return res
