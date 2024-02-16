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

from odoo import fields, models


class ResPartner(models.Model):
    _name='res.partner'
    _inherit='res.partner'
    
    mag_cust_id = fields.Char(string='Customer ID')
    mag_address_id = fields.Char(string='Address ID')
    mag_website_in=fields.Char(string='Created In Shop')
    mag_dob=fields.Date(string='Date Of Birth')
    mag_tax_vat=fields.Char(string='Tax /Vat Number')
    magento_customer = fields.Boolean(string='Magento Customer')
    magento_instance_ids = fields.Many2one('gt.magento.instance', string='Magento Instance')