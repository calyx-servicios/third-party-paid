# -*- coding: utf-8 -*-
##############################################################################
#    Globalteckz Pvt Ltd
##############################################################################

{
    "name" : "Prestashop Connector",
    "version" : "13.1.0.5",
    "depends" : ["sale_stock",'delivery','account','sale_shop','product_images_olbs'],
    "author" : "Globalteckz",
    'summary': 'Manage all your prestashop operations in Odoo',
    'images': ['static/description/Banner.gif'],
    "license" : "Other proprietary",
    "price": "350.00",
    "currency": "EUR",
    "description": """Prestashop E-commerce management""",
    "website" : "https://www.globalteckz.com/shop/odoo-apps/odoo-prestashop-connector/",
    'live_test_url': 'https://www.globalteckz.com/shop/odoo-apps/odoo-prestashop-connector/',
    "category" : "Ecommerce",
    "data" : [
            'security/prestashop_security.xml',
            'security/ir.model.access.csv',
            'data/product_data.xml',
            'data/schedular_data.xml',
	        'data/sequence_data.xml',
            'wizard/create_shop_view.xml',

            'wizard/prestashop_connector_wizard_view.xml',
            'views/prestashop_language_view.xml',
            'views/res_partner_view.xml',
            'views/prestashop_view.xml',
            'views/stock_view.xml',
            'views/prestashop_view.xml',
            'views/product_view.xml',
            'views/cart_rules.xml',
	        'views/prestashop_logs_view.xml',
            'views/catalog_price_rule.xml',
            'views/sale_view.xml',
            # 'views/account_invoice_view.xml',
            'views/order_message_view.xml',
            'views/dashboard_view.xml',
            'views/import_order_workflow.xml',
            'views/sale_shop.xml',

	        'views/prestashop_menus.xml'
    ],
    "active": True,
    "installable": True,
}
 # 'wizard/upload_customer_view.xml',
            # 'wizard/upload_products_view.xml',
            # 'wizard/upload_sale_order_view.xml',
            # 'wizard/upload_category_view.xml',
            # 'wizard/upload_cart_rule_view.xml',
            # 'wizard/catalog_price.xml',
