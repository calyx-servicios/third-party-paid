# -*- coding: utf-8 -*-
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

from odoo import models, fields, api
from odoo.exceptions import UserError
import time

class AccountMove(models.Model):
    _inherit = "account.move"

    mage_invoice_id = fields.Char('Magento Invoice ID', size=100, readonly=True)
    is_magento_id = fields.Boolean('is magento')
    export_magento_sucess = fields.Boolean('Export Magento Sucess')

    def export_magento_invoice(self):
        
        sale_id = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
        invoice_id = self
        if sale_id:
            store = sale_id.magento_shop_id
        
            if store:
                token = False
                if store.magento_instance_id.magento_instance_id_used_token:
                    token = store.magento_instance_id.token
                else:
                    store.magento_instance_id.generate_token()
                    token = store.magento_instance_id.token
                    token = token.replace('"'," ")
                
                headers = {
                    'authorization':"Bearer " + token,
                    'content-type': "application/json",
                    'cache-control': "no-cache",
                    }

                res = store.export_magento_invoice_order(headers, invoice_id, sale_id)

                if res == 'sucess':
                    self.export_magento_sucess = True
            
    def action_post(self):
        res = super(AccountMove, self).action_post()
        sale_id = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
        store = sale_id.magento_shop_id
        if store:
            self.export_magento_invoice()
        return res