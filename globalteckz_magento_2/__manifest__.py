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


{
    'name': 'Odoo Magento 2 Connector',
    'version': '1.1.0.1',
    'category': 'Connector',
    'sequence': 1,
    'author': 'Globalteckz',
    'summary': 'This module will help to handle magento data in odoo and vice-versa',
    'website': 'http://www.globalteckz.com',
    "license" : "Other proprietary",
    'images': ['static/description/Banner.gif'],
    "price": "399.00",
    "currency": "EUR",
    'description': """
magento2
Magento Odoo Connector
Odoo Magento 2 Connector
Odoo13 Magento 2 Connector
odoo magento 2 connector
odoo magento 2
odoo magento 2 integration
odoo magento 2 extension
odoo magento 2 bridge
odoo 13 magento 2
magento 2 connector
magento 2 bridge
magento 2 odoo connector
magento 2 odoo bridge
magento 2 odoo extension
odoo magento2 connector
odoo 13 magento2 connectors
odoo13
odoo12
Magento 2 Odoo 13 Connector
Magento2.0 + Odoo 11 Connector
magento2 connector
magento2 integration
magento integration
magento 2 integration
odoo magento bridge
odoo magento2 bridge
magento2 bridge
magento bridge
bridge magento2
magento 2 extension
magento2 extension
magento2 github
magento 2 github
magento bridge
magento2 bridge
odoo12 magento
odoo 12
magento2
magento2 odoo12
magento 2 odoo12
magento 2 odoo
magento2.5
magento2.4
magento 2.3
magento 2.4
magento 2.5
Magento 2 odoo 10
Magento 2 odoo 11
Magento 2 odoo 12
Magento 2 odoo 13
Magento 2.1 odoo
Magento 2.2 odoo connector
Magento 2 odoo integration
Magento e-Commerce management
Odoo 8 Magento Connector
odoo 8 magento integration
odoo magento connector
odoo magento integration
Odoo 9 Magento Connector
odoo 9 magento integration
odoo magento connector
odoo magento integration
Odoo 10 Magento Connector
odoo 10 magento integration
odoo magento connector
odoo magento integration
Odoo 11 Magento Connector
odoo 11 magento integration
Odoo 12 Magento Connector
odoo 12 magento integration
Odoo 13 Magento Connector
odoo 13 magento integration
odoo magento connector
odoo magento integration
Magento connector
magento integration
Magento 1.9 connector
Magento 1.8 connector
Import sales order from magento
import inventory from magento
import products from magento
import simple products from magento
import shipment from magento
import invoice from magento

    """,
    'depends': [
                'sale',
                'stock',
                'base',
                'account',
                'delivery',
                'product',
            ],
    'data': [
            'data/ir_cron.xml',
            'security/gt_magento_security.xml',
            'security/ir.model.access.csv',
            'views/gt_magento_view.xml',
            'views/product_attribute_views.xml',
            'views/gt_magento_shop_view.xml',
            'views/gt_attribute_set_view.xml',
            'views/gt_attributes_view.xml',
            'views/gt_attribute_option_view.xml',
            'views/gt_magento_website_view.xml',
            'views/product_category_view.xml',
            'views/prodcuct_view.xml',
            'views/partner_view.xml',
            'views/sale_view.xml',
            'views/account_invoice_view.xml',
            'views/stock_picking_view.xml',
            'views/gt_magento_menu.xml',
            'views/product_template_view.xml',
            'views/magento_schedular_data_view.xml',
            ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
