# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)

class ProductTemplateBindToProducteca(models.TransientModel):

    _name = "producteca.binder.wiz"
    _description = "Wizard de Product Template Producteca Binder"
    _inherit = "ocapi.binder.wiz"

    connectors = fields.Many2many("producteca.account", string='Producteca Accounts')

    def product_template_add_to_connector(self, context=None):

        _logger.info("product_template_add_to_connector (Producteca)")
        context = context or self.env.context

        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.template']

        res = {}
        for product_id in product_ids:
            
            product = product_obj.browse(product_id)
                        
            for producteca in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, producteca.name))
                #Binding to
                product.producteca_bind_to( producteca )                                 
                        
                
    def product_template_remove_from_connector(self, context=None):

        _logger.info("product_template_remove_from_connector (Producteca)")
        
        context = context or self.env.context

        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.template']

        res = {}
        for product_id in product_ids:
            
            product = product_obj.browse(product_id)
                        
            for producteca in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, producteca.name))
                #Binding to
                product.producteca_unbind_from( producteca )       
                
                
                
class ProductProductBindToProducteca(models.TransientModel):

    _name = "producteca.variant.binder.wiz"
    _description = "Wizard de Product Variant Producteca Binder"
    _inherit = "ocapi.binder.wiz"

    connectors = fields.Many2many("producteca.account", string='Producteca Accounts')

    def product_product_add_to_connector(self, context=None):

        _logger.info("product_product_add_to_connector (Producteca)")
        
        context = context or self.env.context
        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.product']

        res = {}
        for product_id in product_ids:
            
            product = product_obj.browse(product_id)
                        
            for producteca in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, producteca.name))
                #Binding to
                product.producteca_bind_to( producteca )                                 
                        
                
    def product_product_remove_from_connector(self, context=None):

        _logger.info("product_product_remove_from_connector (Producteca)")

        context = context or self.env.context
        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.product']

        res = {}
        for product_id in product_ids:
            
            product = product_obj.browse(product_id)
                        
            for producteca in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, producteca.name))
                #Binding to
                product.producteca_unbind_from( producteca )       
                
                
                
class StockQuantBindToProducteca(models.TransientModel):

    _name = "producteca.stock.quant.binder.wiz"
    _description = "Wizard de Stock Quant Product Producteca Binder"
    _inherit = "ocapi.binder.wiz"

    connectors = fields.Many2many("producteca.account", string='Producteca Accounts')

    def stock_quant_add_to_connector(self, context=None):

        _logger.info("stock_quant_add_to_connector (Producteca)")
        
        context = context or self.env.context
        company = self.env.user.company_id
        stock_quant_ids = context['active_ids']
        
        stock_quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']

        res = {}
        for stock_quant_id in stock_quant_ids:
            
            stock_quant = stock_quant_obj.browse(stock_quant_id)
            product = stock_quant and stock_quant.product_id
                
            if not product:        
                continue;
                
            for producteca in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, producteca.name))
                #Binding to
                product.producteca_bind_to( producteca )                                 
                        
                
    def stock_quant_remove_from_connector(self, context=None):

        _logger.info("stock_quant_remove_from_connector (Producteca)")

        context = context or self.env.context
        company = self.env.user.company_id
        stock_quant_ids = context['active_ids']
        
        stock_quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']

        res = {}
        for stock_quant_id in stock_quant_ids:
            
            stock_quant = stock_quant_obj.browse(stock_quant_id)
            product = stock_quant and stock_quant.product_id
                        
            if not product:        
                continue;

            for producteca in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, producteca.name))
                #Binding to
                product.producteca_unbind_from( producteca )       
                
                
                
class ProductecaNotificationsProcessWiz(models.TransientModel):
    _name = "producteca.notification.wiz"
    _description = "Producteca Notifications Wiz"

    connection_account = fields.Many2one( "producteca.account", string='Producteca Account',help="Cuenta de producteca origen de la publicación")
    
    def process_notifications( self, context=None ):

        context = context or self.env.context

        _logger.info("process_notifications (Producteca)")
        noti_ids = ('active_ids' in context and context['active_ids']) or []
        noti_obj = self.env['producteca.notification']
        ret = []
        
        try:
            #meli = None
            #if self.connection_account:
                #meli = self.env['meli.util'].get_new_instance( self.connection_account.company_id, self.connection_account )
                #if meli.need_login():
                #    return meli.redirect_login()
            
            ##if not self.connection_account:
            #    raise UserError('Connection Account not defined!')
            for noti_id in noti_ids:

                _logger.info("Processing notification: %s " % (noti_id) )

                noti = noti_obj.browse(noti_id)
                
                if noti:
                    reti = None
                    
                    if self.connection_account and noti.connection_account and noti.connection_account.id==self.connection_account.id:
                        reti = noti.process_notification()
                        
                    if not self.connection_account:
                        reti = noti.process_notification()
                        
                    if reti:
                        ret.append(str(reti))
                    
        except Exception as e:
            _logger.info("process_notifications > Error procesando notificacion")
            _logger.error(e, exc_info=True)
            _logger.error(str(ret))
            #self._cr.rollback()
            raise e
            
        _logger.info("Processing notification result: %s " % (str(ret)) )
        
class ProductecaSaleProcessWiz(models.TransientModel):
    _name = "producteca.sale_order.wiz"
    _description = "Producteca Sale Process Wiz"

    connection_account = fields.Many2one( "producteca.account", string='Producteca Account',help="Cuenta de producteca origen de la publicación")
    
    def producteca_sale_process( self, context=None ):

        context = context or self.env.context

        _logger.info("producteca_sale_process (Producteca)")
        prorder_ids = ('active_ids' in context and context['active_ids']) or []
        prorder_obj = self.env['producteca.sale_order']
        ret = []
        
        try:
            #meli = None
            #if self.connection_account:
                #meli = self.env['meli.util'].get_new_instance( self.connection_account.company_id, self.connection_account )
                #if meli.need_login():
                #    return meli.redirect_login()
            
            ##if not self.connection_account:
            #    raise UserError('Connection Account not defined!')
            for prorder_id in prorder_ids:

                _logger.info("Processing producteca order: %s " % (prorder_id) )

                prorder = prorder_obj.browse(prorder_id)
                
                if prorder:
                    reti = None
                    
                    if self.connection_account and prorder.connection_account and prorder.connection_account.id==self.connection_account.id:
                        reti = prorder.update()
                        
                    if not self.connection_account:
                        reti = prorder.update()
                        
                    if reti:
                        ret.append(str(reti))
                    
        except Exception as e:
            _logger.info("producteca_sale_process > Error procesando orden de producteca")
            _logger.error(e, exc_info=True)
            _logger.error(str(ret))
            #self._cr.rollback()
            raise e
            
        _logger.info("Processing producteca sales result: %s " % (str(ret)) )
