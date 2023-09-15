# -*- coding: utf-8 -*-
{
    'name': "MercadoLibre Uploader",
    'summary': "MercadoLibre Uploader for Odoo.",
    'version': '1.0.6',
    'author': "Calyx Servicios S.A",
    'website': "https://www.calyxservicios.com.ar/",
    'description': """
Odoo MercadoLibre Uploader
==================================================

    """,

    'depends': [
        'base',
        'contacts',
        'product',
        'sale_management',
        'stock',
    ],

    'data': [
        'security/permissions.xml',
        'data/ir_cron.xml',
        'data/res_config_settings.xml',
        'data/res_currency.xml',
        'data/site_ids.xml',
        'data/ir_config_parameter.xml',
        'views/menus.xml',
        'views/settings.xml',
        'views/product_template.xml',
        'views/test_users.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/product_pricelist.xml',
        'views/categories.xml',
        'views/product_attribute.xml',
        'views/shipping_methods.xml',
        'views/publications.xml',
        'views/publications_variants.xml',
        'views/product_attribute_value.xml',
    ],

    'application': True,
    'price': 2569,
    'currency': 'USD',
    'images': [
        'static/description/images/settings_instance_authenticated_screenshot.png',
        'static/description/images/product_ready_for_publish.png',
        'static/description/images/product_category_attributes.png',
        'static/description/images/product_attributes.png',
        'static/description/images/pricelist_example.png',
    ],
    'license': 'OPL-1',
}
