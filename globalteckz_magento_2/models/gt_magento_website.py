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


class Gtebsite(models.Model):
    _name= 'gt.magento.website'
    _description = 'Magento Website'
     
     
    name = fields.Char(string='Name',size=64, required=True)
    magento_instance_id = fields.Many2one('gt.magento.instance',string='Instance',readonly=True)
    magento_website =  fields.Boolean(string='Magento Shop',readonly=True)
    code =  fields.Char(string='Code', size=64,readonly=True)
    website_id =  fields.Integer(string='Website ID',readonly=True)
    default_group_id = fields.Integer(string='Default Group ID')
    
    