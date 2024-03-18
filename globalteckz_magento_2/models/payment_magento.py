# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz
#    Copyright (C) 2013-Today Globalteckz (http://www.globalteckz.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields,models,api
import requests
import json
from odoo.exceptions import UserError
import logging
logger = logging.getLogger('product')

class PaymentMethodMagento(models.Model):
    _name = "payment.method.magento"
    _description = 'Magento payment Method'
    
    name =  fields.Char('Name')
    code =  fields.Char('code')
    

    def create_payment_method(self, shop_data, headers, order_id):
        url = f"{shop_data.magento_instance_id.location}/rest/V1/orders/{order_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            order_data = response.json()
            payment_data = order_data.get('payment', {})
            payment_method_code = payment_data.get('method')
            payment_method_title = payment_data['additional_information'][0]         
            if payment_method_code:
                mag_id = self.search([('code', '=', payment_method_code)])
                if not mag_id:
                    met_id = self.create({'name': payment_method_title, 'code': payment_method_code})
                    return met_id
                else:
                    if mag_id['name'] != payment_method_title:
                        mag_id.write({'name': payment_method_title})
                self._cr.commit()
                return True
            else:
                return False
        else:
            logger.error(f"Error fetching order details. Status Code: {response.status_code}")
            return False