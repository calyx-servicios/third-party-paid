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


class Picking(models.Model):
    _inherit='stock.picking'

    mage_stock_id = fields.Char(string= 'Magento ID',readonly=True)
    is_magento=fields.Boolean('is magento')
    


class DeliveryCarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = "delivery.carrier"


    mage_delivery = fields.Boolean(string='Delivery')
    magento_code = fields.Char('Magento Code', size=64)
    magento_export = fields.Char('Magento Export', size=64)