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


class PaymentMethodMagento(models.Model):
    _name = "payment.method.magento"
    _description = 'Magento payment Method'
    
    name =  fields.Char('Name')
    code =  fields.Char('code')
    
    

    def create_payment_method(self,shop_data,headers,payment_id):
        url=str(shop_data.magento_instance_id.location)+"/rest/V1/carts/"+str(payment_id)+"/payment-methods"
        response = requests.request("GET",url, headers=headers) 
        if str(response.status_code)=="200":
            payment_code=json.loads(response.text)
            if payment_code:
                for payment in payment_code:
                    mag_id = self.search([('code','=',payment.get('code'))])
                    if not mag_id:
                        self.create({'name':payment['title'], 'code':payment['code']})
        
            self._cr.commit()
        return True