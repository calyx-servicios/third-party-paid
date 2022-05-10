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
    'name': 'Odoo13 shopify connector',
    'version': '10.0',
    'category': 'Generic Modules',
    'sequence': 1,
    'author': 'Globalteckz',
    'website': 'http://www.globalteckz.com',
    "price": "399.00",
    "currency": "USD",
    'images': ['static/description/Banner.gif'],
    'summary': 'Odoo Shopify Connector',
    'description': """
Shopify Odoo Connector
Odoo shopify connector
odoo 10 shopify connector
odoo 11 shopify connector 
odoo 10 shopify integration 
odoo 11 shopify integration
odoo 12 shopify
odoo12 shopify
odoo 13 shopify
odoo13 shopify
shopify 12
shopify12
odoo12 shopify connector
odoo12 shopify integration
shopify13
odoo13 shopify connector
odoo13 shopify integration
Other connectors :
Odoo ebay connector 
odoo ebay integration
odoo amazon connector
odoo amazon integration
odoo prestashop connector
odoo prestashop integration
oodo shopify connector
oodo shopify integration
    """,
    'depends': ['sale','stock','base','delivery','account'],
    'data': [
            'security/shopify_access_rule.xml',
            'security/shopify_security.xml',
            'security/ir.model.access.csv',
            'views/gt_shopify_instance_view.xml',
            #'views/res_config_view.xml',
            'views/gt_shopify_store.xml',
            'views/product_template_view.xml',
            'views/product_product_view.xml',
            'views/res_partner_view.xml',
            'views/sale_order_view.xml',
            'views/gt_shopify_log_view.xml',
            'views/gt_import_order_workflow.xml',
            'wizard/dashboard_wizard_view.xml',
            'views/account_invoice_view.xml',
            'views/gt_dashboard_view.xml',
            'views/stock_picking_view.xml',
            'views/delivery_carrier_view.xml',
            'views/schedular_view.xml',
            'views/stock_location_view.xml',
            'views/gt_shopify_menu.xml',
            
            ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
