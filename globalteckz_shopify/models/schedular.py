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


from odoo import fields,api,models
import requests
import json
import datetime
import base64
import urllib
import math
from datetime import date
import logging
logger = logging.getLogger('product')
import urllib.request

class GTShopifyInstance(models.Model):
    _inherit='gt.shopify.instance'
    
    
    
    def gt_shopify_import_order_schedular(self, cron_mode=True):
        print ("gt.shopify.instance++++++++ import order function called ")
        instance_id = self.search([])
        for instance in instance_id:
            print ('instance++++++++++++++',instance)
            instance.gt_import_shopify_orders()
            print ('successfull')
        return True