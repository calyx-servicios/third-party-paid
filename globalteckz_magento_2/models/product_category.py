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

from odoo import fields,models,api, _
import requests
import json

class ProductCategory(models.Model):
    _inherit='product.category'
    
    
    magento_id = fields.Char(string='Code')
    position = fields.Integer(string='Position')
    level = fields.Integer(string='Level')
    magento_instance_id = fields.Many2one('gt.magento.instance', string='Magento Instance')
    category_exported = fields.Boolean(string='Category Exported')
    shop_id = fields.Many2one('gt.magento.store',string='Magento Shop')
    
    
    
    
    def GtExportMagentoCategory(self):
        self.magento_instance_id.generate_token()
        token=self.magento_instance_id.token
        token=token.replace('"'," ")
        auth_token="Bearer "+token.strip()
        auth_token=auth_token.replace("'",'"')
        headers = {
            'authorization':auth_token,
            'content-type': "application/json",
            'cache-control': "no-cache",
            }
        if self.category_exported == False:
            vals = {
                "category": {
                  "parentId": str(self.parent_id.magento_id) if self.parent_id else 0,
                  "name": str(self.name),
                  "isActive": "true",
                  "includeInMenu": "true",
                }
              }
            url=str(self.magento_instance_id.location)+"/rest/"+ str(self.shop_id.code) +"/V1/categories"
            productload= str(vals) 
            productload=productload.replace("'",'"')  
            productload=str(productload)
            response = requests.request("POST",url,data=productload, headers=headers)
            print("==========response>>>>>>>>>>",response)
            if str(response.status_code)=="200":
                each_response=json.loads(response.text)
                ids = each_response['id']
                self.write({'category_exported':True,'magento_id':ids})
        return True