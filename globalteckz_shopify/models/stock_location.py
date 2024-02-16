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


from odoo import fields,models, api

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    
    gt_shopify_location = fields.Boolean(string='Shopify Location',readonly=True)
    gt_shopify_location_id = fields.Char(string='Shopfy Location ID',readonly=True)
    

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    
    gt_shopify_exported = fields.Boolean(string='Shopify Exported')