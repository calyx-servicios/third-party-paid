# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Promotion',
    'version': '13.1.1',
    'summary': 'Support most of basic promotion programs for your business. Simple and Easy UI help you understand quickly how to setup promotion in POS',
    'sequence': 30,
    'description': """
    Odoo Pos Promotion
    """,
    'category': 'Point of Sale',
    'depends': [
        'point_of_sale'
    ],
    'live_test_url': 'https://demo13.fauniq.com',
    'data': [
        # data
        'data/ir_cron_data.xml',
        'data/pos_promotion_type_data.xml',

        # views
        'views/pos_order_views.xml',
        'views/pos_promotion_views.xml',
        'views/pos_promotion_type_views.xml',

        # wizards
        'wizards/import_product_promotion.xml',

        # reports
        'reports/pos_order_report_view.xml',

        # asset
        'views/point_of_sale_assets.xml',

        # security
        'security/ir.model.access.csv'
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'price': 99,
    'currency': 'EUR',
    'license': 'OPL-1',
    'support': 'fauniq.erp@gmail.com',
    'author': "Fauniq",
    'website': 'fauniq.com',
    'images': ['images/main_image.png'],
    'installable': True,
    'application': False,
    'auto_install': False
}
