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


import json
from openerp import api, fields, models


class GTShopifyStore(models.Model):
    _inherit = 'gt.shopify.instance'
    _description = "Shopify Instance Dashboard view"
    
    shopify_kanban_instance = fields.Text(compute='_shopify_kanban_instace')

    
    
    def _shopify_kanban_instace(self):
        order_obj = self.env['sale.order']
        invoice_obj = self.env['account.invoice']
        stock_obj = self.env['stock.picking']
        product_obj = self.env['product.template']
        product_product_obj = self.env['product.product']
        log_obj = self.env['shopify.log']
        #shop_obj = self.env['sale.shop']
        #shop_id  = shop_obj.search([('prestashop_instance_id','=',self.id)])
        all_order_ids = order_obj.search([('gt_shopify_instance_id','=',self.id)])
        pending_order_ids = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','!=','done')])
        complete_order_ids = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','=','done')])
        draft_order_ids = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','=','draft')])
        cancel_order_ids = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','=',True),('state','=','cancel')])
        
        origin_list = [s.name for s in all_order_ids]
        
        all_invoice_ids = invoice_obj.search([('origin', 'in', origin_list)])
        draft_invoice_ids = invoice_obj.search([('origin', 'in', origin_list),('state','=','draft')])
        open_invoice_ids = invoice_obj.search([('origin', 'in', origin_list),('state','=','open')])
        paid_invoice_ids = invoice_obj.search([('origin', 'in', origin_list),('state','=','paid')])
#        
        waiting_availability_stock_ids = stock_obj.search([('origin', 'in', origin_list),('state','=', 'confirmed')])
        available_stock_ids = stock_obj.search([('origin', 'in', origin_list),('state','=', 'assigned')])
        complete_stock_ids = stock_obj.search([('origin', 'in', origin_list),('state','=','done')])
        product_template_exported_ids = product_obj.search([('gt_shopify_instance_id', '=', self.id),('gt_shopify_product','=',True),('gt_shopify_exported','=',True)])
        product_template_not_exported = product_obj.search([('gt_shopify_instance_id', '=', self.id),('gt_shopify_product','=',True),('gt_shopify_exported','=',False)])
        product_variant_exported = product_product_obj.search([('gt_shopify_instance_id', '=', self.id),('gt_shopify_product','=',True),('gt_shopify_exported','=',True)])
        product_variant_not_exported = product_product_obj.search([('gt_shopify_instance_id', '=', self.id),('gt_shopify_product','=',True),('gt_shopify_exported','=',False)])
        shopify_logs = log_obj.search([('gt_shopify_instance_id', '=', self.id)])
        shopify_webservices ={

        'all_order': len(all_order_ids),
        'pending_order': len(pending_order_ids),
        'complete_order': len(complete_order_ids),
        'draft_order': len(draft_order_ids),
        'cancel_order': len(cancel_order_ids),
        'draft_invoice': len(draft_invoice_ids),
        'open_invoice': len(open_invoice_ids),
        'paid_invoice': len(paid_invoice_ids),
        'waiting_availability_stock': len(waiting_availability_stock_ids),
        'available_stock': len(available_stock_ids),
        'complete_stock': len(complete_stock_ids),
        'product_template_exported' : len(product_template_exported_ids),
        'product_template_not_exported' : len(product_template_not_exported),
        'product_variant_exported' : len(product_variant_exported),
        'product_variant_not_exported' : len(product_variant_not_exported),
        'shopify_logs' : len(shopify_logs),
#                 'late_delivey':late_delivey_ids,
#                 'back_order': len(back_order_ids),
        }
        self.shopify_kanban_instance = json.dumps(shopify_webservices)

    
    def action_view_all_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id)])
        imd = self.env['ir.model.data']
        action = self.env.ref('globalteckz_shopify.action_orders_shopify_all')
        list_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_tree')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % order_id.ids
        }
        if len(order_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = order_id.ids[0]
        elif len(order_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    def action_view_draft_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','=','draft')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_tree')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain':[('store_id','=', self.id),('state','=','draft')]
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    def action_view_cancel_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','=','cancel')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_tree')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain':[('store_id','=', self.id),('state','=','cancel')]
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
#         elif len(order_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = order_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    
    def action_view_pending_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','!=','done')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_tree')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain':[('store_id','=', self.id),('state','!=','done')]
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    
    def action_view_complete_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False),('state','!=','done')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_tree')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.view_order_inherit_shopify_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain':[('store_id','=', self.id),('state','=','done')]
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    
    
    def action_view_draft_invoice(self):
        order_obj = self.env['sale.order']
        invoic_obj = self.env['account.invoice']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False)])
        origins = [order.name for order in order_id]
        invoice_id = invoic_obj.search([('origin','in',origins),('state','=','draft')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % invoice_id.ids
        }
        print ("result", result)
        if len(invoice_id) == 1:
          result['views'] = [(form_view_id, 'form')]
          result['res_id'] = invoice_id.ids[0]
        elif len(invoice_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    def action_view_open_invoice(self):
        order_obj = self.env['sale.order']
        invoic_obj = self.env['account.invoice']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False)])
        origins = [order.name for order in order_id]
        invoice_id = invoic_obj.search([('origin','in',origins),('state','=','open')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % invoice_id.ids
        }
        print ("result", result)
        if len(invoice_id) == 1:
          result['views'] = [(form_view_id, 'form')]
          result['res_id'] = invoice_id.ids[0]
        elif len(invoice_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result
 
    
    def action_view_paid_invoice(self):
        order_obj = self.env['sale.order']
        invoic_obj = self.env['account.invoice']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False)])
        origins = [order.name for order in order_id]
        invoice_id = invoic_obj.search([('origin','in',origins),('state','=','paid')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % invoice_id.ids
        }
        print ("result", result)
        if len(invoice_id) == 1:
          result['views'] = [(form_view_id, 'form')]
          result['res_id'] = invoice_id.ids[0]
        elif len(invoice_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result	
    
    
    def action_view_waiting_availability_stock(self):
        order_obj = self.env['sale.order']
        stock_obj = self.env['stock.picking']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False)])
        origins = [order.name for order in order_id]
        stock_id = stock_obj.search([('origin','in',origins),('state','=', 'confirmed')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % stock_id.ids
        }
        print ("result", result)
        if len(stock_id) == 1:
          result['views'] = [(form_view_id, 'form')]
          result['res_id'] = stock_id.ids[0]
        elif len(stock_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result    
    
    
    def action_view_available_stock(self):
        order_obj = self.env['sale.order']
        stock_obj = self.env['stock.picking']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False)])
        origins = [order.name for order in order_id]
        stock_id = stock_obj.search([('origin','in',origins),('state','=', 'assigned')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % stock_id.ids
        }
        print ("result", result)
        if len(stock_id) == 1:
          result['views'] = [(form_view_id, 'form')]
          result['res_id'] = stock_id.ids[0]
        elif len(stock_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    
    def action_view_complete_stock(self):

        order_obj = self.env['sale.order']
        stock_obj = self.env['stock.picking']
        order_id = order_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_order','!=',False)])
        origins = [order.name for order in order_id]
        stock_id = stock_obj.search([('origin','in',origins),('state','=', 'done')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % stock_id.ids
        }
        print ("result", result)
        if len(stock_id) == 1:
          result['views'] = [(form_view_id, 'form')]
          result['res_id'] = stock_id.ids[0]
        elif len(stock_id) == 0:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    
    def action_view_product_template_exported(self):
        product_obj = self.env['product.template']
        product_id = product_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_product','!=',False),('gt_shopify_exported','=', True)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('globalteckz_shopify.shopify_product_template_exported')
        list_view_id = imd.xmlid_to_res_id('product.product_template_tree_view')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.gt_view_product_template_shopify')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            
        }
        if len(product_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % product_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    
    def action_view_product_template_not_exported(self):
        product_obj = self.env['product.template']
        product_id = product_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_product','!=',False),('gt_shopify_exported','=', False)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('globalteckz_shopify.shopify_product_template_not_exported')
        list_view_id = imd.xmlid_to_res_id('product.product_template_tree_view')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.gt_view_product_template_shopify')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            
        }
        if len(product_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % product_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    def action_view_product_variant_exported(self):
        product_obj = self.env['product.product']
        product_id = product_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_product','!=',False),('gt_shopify_exported','=', False)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('globalteckz_shopify.shopify_products_variant_exported')
        list_view_id = imd.xmlid_to_res_id('product.product_product_tree_view')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.gt_view_product_product_shopify')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            
        }
        if len(product_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % product_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    def action_view_product_variant_not_exported(self):
        product_obj = self.env['product.template']
        product_id = product_obj.search([('gt_shopify_instance_id','=',self.id),('gt_shopify_product','!=',False),('gt_shopify_exported','=', False)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('globalteckz_shopify.shopify_products_variant_not_exported')
        list_view_id = imd.xmlid_to_res_id('product.product_product_tree_view')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.gt_view_product_product_shopify')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            
        }
        if len(product_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % product_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    def action_view_workflow_settings(self):
        workflow_obj = self.env['gt.import.order.workflow']
        workflow_id = workflow_obj.search([('id','=',self.gt_worflow_id.id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('globalteckz_shopify.action_import_order_workflow_gt')
#        list_view_id = imd.xmlid_to_res_id('product.product_product_tree_view')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.gt_import_order_workflow_form_view')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[False, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            
        }
        if len(workflow_id) == 1:
            result['domain'] = "[('id','in',%s)]" % workflow_id.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    
    def action_view_shopify_logs(self):
        log_obj = self.env['shopify.log']
        log_ids = log_obj.search([('gt_shopify_instance_id','=',self.id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('globalteckz_shopify.action_shopify_log_view')
        list_view_id = imd.xmlid_to_res_id('product.gt_view_shopify_log_tree')
        form_view_id = imd.xmlid_to_res_id('globalteckz_shopify.gt_view_shopify_log_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            
        }
        if len(log_ids) >= 1:
            result['domain'] = "[('id','in',%s)]" % log_ids.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
     