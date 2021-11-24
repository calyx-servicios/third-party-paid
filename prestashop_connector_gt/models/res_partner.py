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
from datetime import date,datetime


class res_partner(models.Model):
    _inherit = "res.partner"
                
    date_of_birth=fields.Date('Date Of Birth')
    prestashop_customer=fields.Boolean('Prestashop customer', default=False)
    prestashop_supplier=fields.Boolean('Prestashop Supplier',default=False)
    prestashop_address=fields.Boolean('Prestashop Address',default=False)
    prestashop_paswrd=fields.Char('Password')
    presta_id = fields.Char('Presta ID')

    shop_ids = fields.Many2many('sale.shop', 'customer_shop_rel', 'cust_id', 'shop_id', string="Shop")
    manufacturer = fields.Boolean(string="Is Manufacturer?",default=False)
    to_be_exported = fields.Boolean(string="To be exported?",default=False)
    address_id = fields.Char('Address ID')
    alias = fields.Char(string="Alias")
    # newsletter = fields.Boolean(string="Subscribed for newsletter?")
    # ads_opt_in = fields.Boolean(string="Opted in for ads?")
