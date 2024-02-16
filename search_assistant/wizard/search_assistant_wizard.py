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

from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)


class SearchAssistantLine(models.TransientModel):
    """
    """
    _name = "search.assistant.line"
    _description = "Search Assistant Line"

    search_id = fields.Many2one('search.assistant', string='Search')
    selected = fields.Boolean(string='')
    description = fields.Char('Description')
    attribute_value_ids = fields.Many2many(
        'product.template.attribute.value', string="Attribute Values")
    product_id = fields.Many2one('product.product', string='Product')
    brand_id = fields.Many2one(
        'product.brand', string="Brand")
    product_uom_qty = fields.Float(
        string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)

    # Please check sale_stock module for a similiar use of this calculation fields. I took part of this code from there.
    virtual_available_at_date = fields.Float(compute='_compute_qty_at_date')
    scheduled_date = fields.Datetime(compute='_compute_qty_at_date')
    free_qty_today = fields.Float(compute='_compute_qty_at_date')
    qty_available_today = fields.Float(string='Stock',compute='_compute_qty_at_date')
    warehouse_id = fields.Many2one('stock.warehouse', compute='_compute_qty_at_date')
    qty_to_deliver = fields.Float(compute='_compute_qty_to_deliver')

    @api.depends('product_id', 'product_uom_qty', 'search_id.warehouse_id','search_id.stock_date')
    def _compute_qty_at_date(self):
        """ Please see at sale_stock module. I took part of this code from there."""
        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['search.assistant.line'])
        stock_date = self.search_id.stock_date or fields.Datetime.now() 
        warehouse_id =self.search_id.warehouse_id.id
        for line in self:
            grouped_lines[(warehouse_id, stock_date)] |= line

        treated = self.browse()
        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
                'qty_available',
                'free_qty',
                'virtual_available',
            ])
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
                line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[line.product_id.id]
                if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom)
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom)
                    line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom)
                qty_processed_per_product[line.product_id.id] += line.product_uom_qty
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False



class SearchAssistant(models.TransientModel):
    """
    """
    _name = "search.assistant"
    _description = "Search Assistant"

    @api.model
    def _default_partner_id(self):
        """
        """
        return False
    
    @api.model
    def _default_warehouse_id(self):
        """
        """
        return False

    @api.model
    def _default_partner_readonly(self):
        """
        """
        return False

    @api.model
    def _default_stock_date(self):
        """
        """
        return fields.Datetime.now() 

    @api.model
    def _default_warehouse_id(self):
        company = self.env.company.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    partner_readonly = fields.Boolean(string='Partner Readonly', default=_default_partner_readonly)

    partner_id = fields.Many2one(
        'res.partner', string='Partner', default=_default_partner_id, required=True)
    
    brand_ids = fields.Many2many(
        'product.brand', string="Brands")

    attribute_ids = fields.Many2many(
        'product.attribute', string='Product Attribute')
    
    attribute_value_ids = fields.Many2many(
        'product.template.attribute.value', string="Attribute Values")
    category_ids = fields.Many2many(
        'product.category', string="Product Category")
    code = fields.Char(string='Code')

    description = fields.Char(string='Description',
                              help='Enter the description spaces split your query in \
                                    case you forgot how was your product description.')
    line_ids = fields.One2many(
        'search.assistant.line', 'search_id', string='Search Results')
    selected = fields.Boolean('')
    warehouse_id = fields.Many2one('stock.warehouse', default=_default_warehouse_id)

    stock_date = fields.Datetime('Stock Date', default=_default_stock_date, required=True)

    def make_domain(self, domain_name, code):
        """
        This function builds a domain spliting the code by spaces
        """
        domain_code= [(domain_name,'ilike','%')]
        if code:
            i=code.find(' ')
            domain_code=[]
            while i!= -1:
                domain_code.append((domain_name,'ilike',code[0:i]))
                code=code[i+1:]
                i=code.find(' ')
            domain_code.append((domain_name,'ilike',code))
        return domain_code


    def _get_domain_filter(self):
        """
        """
        _logger.debug('====> filter activated ====>')
        _logger.debug(self._context.get('active_model'))
        product_obj = self.env['product.product']
        product_attribute_obj = self.env['product.template.attribute.value']
        domain = []
        
        attribute_ids = list(set(self.attribute_ids.ids))
        brand_ids = list(set(self.brand_ids.ids))
        attribute_values_ids = list(set(self.attribute_value_ids.ids))
        category_ids = list(set(self.category_ids.ids))
        description = self.description
        code = self.code

        if description and len(description)>0:
            for description_domain in self.make_domain('name',description):
                domain.append(description_domain)
        if code and len(code)>0:
            for code_domain in self.make_domain('default_code',code):
                domain.append(code_domain)
        
        if len(attribute_values_ids)>0:
            domain.append(('product_template_attribute_value_ids', 'in', attribute_values_ids))
        else:
            if len(attribute_ids)>0:
                attribute_ids=product_attribute_obj.search([('attribute_id','in',attribute_ids)]).ids
                domain.append(('product_template_attribute_value_ids', 'in', attribute_ids))
        if len(brand_ids)>0:
            domain.append(('product_brand_id', 'in', brand_ids))

        if len(category_ids)>0:
            domain.append(('categ_id', 'in', category_ids))
        _logger.debug('====> DOMAIN ====> %s' % domain)
        return domain

    def _get_selected_products(self):
        return None

    def _search(self, selected_products=None):
        product_obj = self.env['product.product']
        self.line_ids = False
        domain=self._get_domain_filter()
        if len(domain)>0:
            product_ids = product_obj.search(domain)
            line_ids = []
            search_line_obj = self.env['search.assistant.line']
            now = fields.Datetime.now()
            
            for product in product_ids:
                selected = self.selected
                if not self.selected and selected_products:
                    selected = selected_products and product.id in selected_products
                
                line_ids.append((0, 0, {
                    'selected': selected,
                    'product_id': product.id,
                    'attribute_value_ids': False,
                    'attribute_value_ids': [(6, 0, product.product_template_attribute_value_ids.ids)],
                    'brand_id': product.product_tmpl_id.product_brand_id and product.product_tmpl_id.product_brand_id.id,
                    'price_unit': product.list_price or 0.0,
                    'qty_available_today': 0.0,
                    'description': product.description or '',
                }))


            self.line_ids = line_ids
    
    
    @api.onchange('attribute_ids','attribute_value_ids','description','selected','category_ids','code','brand_ids')
    def search(self):
        """
        """
        self._search(selected_products=None)

    
