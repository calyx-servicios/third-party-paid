# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp
from ast import literal_eval
import logging

_logger = logging.getLogger(__name__)


class SearchAssistantLine(models.TransientModel):
    """
    """
    _inherit = "search.assistant.line"


class SearchAssistant(models.TransientModel):
    """
    """
    _inherit = "search.assistant"
    _description = "Search Assistant"

    @api.model
    def _default_purchase_order_id(self):
        """
        """
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            return self._context.get('active_id', False)

    @api.model
    def _default_partner_readonly(self):
        """
        """
        value=super(SearchAssistant,self)._default_partner_readonly()
        if self._context.get('update',False)=='purchase.order':
            value=self._default_purchase_order_id()
        return value

    @api.model
    def _default_partner_id(self):
        """
        """
        value=super(SearchAssistant,self)._default_partner_id()
        if self._context.get('create',False)=='purchase.order':
            
                purchase_default_partner_id = self.env['ir.config_parameter'].sudo().get_param(
                    'search_assistant.purchase_default_partner_id', default='False')
                value = literal_eval(purchase_default_partner_id)
        if self._context.get('active_model',False)=='purchase.order':
            if self._context.get('active_id',False):
                    value = self.env['purchase.order'].browse(self._context.get('active_id',False)).partner_id.id
           
        return value

    @api.model
    def _compute_partner_readonly(self):
        """
        """
        value=super(SearchAssistant,self)._compute_partner_readonly()
        if self._context.get('create',False)=='purchase.order':
            return self._default_purchase_order_id()
    
    @api.model
    def _default_warehouse_id(self):
        value = super(SearchAssistant, self)._default_warehouse_id()
        if self._context.get('active_model', False) == 'sale.order':
            if self._context.get('active_id', False):
                value = self.env['sale.order'].browse(
                    self._context.get('active_id', False)).warehouse_id.id
        return value
    
    partner_id = fields.Many2one(
        'res.partner', string='Partner', default=_default_partner_id, required=True)

    partner_readonly = fields.Boolean(string='Partner Readonly', default=_default_partner_readonly)

    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', default=_default_purchase_order_id)

    warehouse_id = fields.Many2one('stock.warehouse', default=_default_warehouse_id)
    
    def action_view_purchase_order(self, purchase_order_id):

        action = self.env.ref('purchase.purchase_order_action_generic').read()[0]

        form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['views'] = form_view
        action['res_id'] = purchase_order_id
        _logger.debug(action)
        return action

    
    def _get_purchase_line_values(self, product_id, quantity, purchase_order_id):
        line_obj = self.env['purchase.order.line']
        values = {
                'name': '',
                'order_id': purchase_order_id,
                'product_id': product_id,
                'price_unit': 0.0,
                'product_qty': quantity
            }
        draft_line = line_obj.new(values)
        draft_line.onchange_product_id()
        values.update({
                'product_uom':draft_line.product_uom.id,
                'date_planned':draft_line.date_planned,
                'price_unit': draft_line.price_unit,
                'display_type': draft_line.display_type
                })
        return values
    
    def _get_selected_products(self):
        value =super(SearchAssistant,self)._get_selected_products()
        if self._context.get('active_model') == 'purchase.order':
            value = set([line.product_id.id for line in self.purchase_order_id.order_line])
        return value

    @api.onchange('attribute_ids','attribute_value_ids','description','selected','category_ids','code','brand_ids')
    def search(self):
        selected_products=self._get_selected_products()
        self._search(selected_products=selected_products)


    def create_purchase_order(self):
        """

        """
        line_obj = self.env['purchase.order.line']
        purchase_obj = self.env['purchase.order']
        lines = []
        must = False

        if self.partner_id:
            for search_wizard in self:
                selection = [
                    line for line in search_wizard.line_ids if line.selected]
                if len(selection) > 0:
                    purchase_order = purchase_obj.create({'partner_id': self.partner_id.id})
                    for line in search_wizard.line_ids:
                        if line.selected:
                            line_obj.create(self._get_purchase_line_values(line.product_id.id,
                                                                    line.product_uom_qty, purchase_order.id))
                    return self.action_view_purchase_order(purchase_order.id)

    def add_purchase_order_items(self):
        """
        Updates item list based on selection. 
        """

        line_obj = self.env['purchase.order.line']
        for search_wizard in self:
            if self.purchase_order_id:
                exists = [
                    line.product_id.id for line in search_wizard.purchase_order_id.order_line]
                selection = [
                    line.product_id.id for line in search_wizard.line_ids if line.selected]

                if len(selection) > 0:
                    for line in search_wizard.line_ids:
                        if line.selected and line.product_id.id not in exists:
                            line_obj.create(self._get_purchase_line_values(line.product_id.id,
                                                                        line.product_uom_qty, 
                                                                        search_wizard.purchase_order_id.id))

            return {'type': 'ir.actions.act_window_close'}
    

    def trim_purchase_order_items(self):
        """
        Trim selected items from document
        """

        line_obj = self.env['purchase.order.line']
        for search_wizard in self:
            if self.sale_order_id:
                exists = set([
                    line.product_id.id for line in search_wizard.purchase_order_id.order_line])
                selection = set([
                    line.product_id.id for line in search_wizard.line_ids if line.selected])
                trim=[s for s in selection if s in exists]
                for line in search_wizard.purchase_order_id.order_line:
                    if line.product_id.id in trim:
                        line.unlink()

            return {'type': 'ir.actions.act_window_close'}
    
 