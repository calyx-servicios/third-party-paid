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


from odoo import api, fields, models

class GtImportOrderWorkflow(models.Model):
    _name = "gt.import.order.workflow"
    _description = "The Shopify Workflow"
    
    @api.model
    def _get_default_journal(self):
#         sale_journal = self.env.ref('globalteckz_magento_2.magento_sales_journal')
#         print "sale_journal", sale_journal.id
        return True # sale_journal.id
    
    stock_location_id = fields.Many2one('stock.location',string='Stock Location')
    real_order_status_update = fields.Boolean(string='Real update order status')
    real_inventory_update = fields.Boolean(string="Real Inventory Update")
    name = fields.Char(string="Name")
    reserve_qty=fields.Boolean('Reserve quantity')
    ship_product=fields.Many2one('product.product',string='Ship Product')
    discount_product=fields.Many2one('product.product',string='Discount Product')
    partner_id = fields.Many2one('res.partner',string='Partner')
    validate_order = fields.Boolean(string="Validate Order")
    create_invoice = fields.Boolean(string="Create Invoice")
    validate_invoice = fields.Boolean(string="Validate Invoice")
    register_payment = fields.Boolean(string="Register Payment")
    complete_shipment = fields.Boolean(string="Complete Shipment")
    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities'),
         ('cost', 'Invoice based on time and material')],
        string='Invoicing Policy', default='order')
    sale_journal = fields.Many2one('account.journal',string='Account Journal')
    pricelist_id = fields.Many2one('product.pricelist','Pricelist')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    company_id = fields.Many2one('res.company',string="Company")
    # from here the additional field is adding
    ship_expo_shopify= fields.Selection(
        [('oncreation', 'Oncreation'),
         ('done', 'Done'),],
        string='Shipment export magento', default='oncreation',
        help="Select the option at which the shipment should "\
        "be exported to magento")


