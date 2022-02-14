# -*- coding: utf-8 -*-
#############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
import socket
from datetime import timedelta, datetime, date, time
import time



class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    is_presta=fields.Boolean('Prestashop')
    # shop_ids = fields.Many2many('sale.shop', 'stock_shop_rel', 'product_id', 'shop_id', string="Shop")

    # @api.model
    def create(self, vals):
        sale_ids = self.env['sale.order'].search([('name', '=', vals.get('origin'))])
        if sale_ids:
            if sale_ids[0].presta_id:
                vals.update({'is_presta': True})
        return super(StockPicking, self).create(vals)


class delivery_carrier(models.Model):
    _inherit = 'delivery.carrier'

    presta_id = fields.Char(string="Presta ID")
    delay_comment = fields.Char(string="Delay")
    is_presta = fields.Boolean(string="Presta")
    shop_ids = fields.Many2many('sale.shop', 'carrier_shop_rel', 'product_id', 'shop_id', string="Shop")
    
    
class StockMove(models.Model):
   _inherit = 'stock.move'
   
   # @api.multi
   def action_done(self):
       sale_shop_obj = self.env['sale.shop']
       res = super(StockMove, self).action_done()
       for rec in self:
           query = "select shop_id from product_templ_shop_rel where product_id = %s "%(rec.product_id.product_tmpl_id.id)
           self.env.cr.execute(query)
           shops = self.env.cr.fetchall()
           if shops != None:
               shops = [i[0] for i in shops]
               for shop in sale_shop_obj.browse(shops):
                   if shop.on_fly_update_stock:
                        shop.with_context(product_ids=[rec.product_id.product_tmpl_id.id]).update_presta_product_inventory()
       return res

