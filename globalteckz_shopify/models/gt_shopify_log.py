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


from odoo import fields, models

class MagentoLog(models.Model):
    _name='shopify.log'
    _description = "The Shopify Log"
   
    name = fields.Char('name')
    description = fields.Char('Log Description')
    res_id = fields.Integer('Resource')
    create_date = fields.Datetime(string="Create Date")
    shopify_log_details_id = fields.One2many('shopify.log.details', 'shopify_log_id', string='Shopify Log Details')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')



class MagentoLogDetails(models.Model):
    _name='shopify.log.details'
    _description = "The Shopify Log Details"
    
    name = fields.Char('name')
    description = fields.Char('Log Description')
    create_date = fields.Datetime(string="Create DateTime")
    shopify_log_id = fields.Many2one('shopify.log', string='Shopify Log')
    