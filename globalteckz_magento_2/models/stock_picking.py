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
from odoo import fields,models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit='stock.picking'

    mage_stock_id = fields.Char(string= 'Magento ID',readonly=True)
    is_magento=fields.Boolean('is magento')
    export_magento_sucess = fields.Boolean('Export Magento Sucess')
    
    def export_magento_shipment_delivery(self):
        
        store = self.sale_id.magento_shop_id
        
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

            res = store.export_magento_shipment_order(headers, self, self.sale_id)
            if res == 'sucess':
                self.export_magento_sucess = True
            
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.sale_id.magento_shop_id:
            self.export_magento_shipment_delivery()
        return res

class DeliveryCarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = "delivery.carrier"


    mage_delivery = fields.Boolean(string='Delivery')
    magento_code = fields.Char('Magento Code', size=64)
    magento_export = fields.Char('Magento Export', size=64)