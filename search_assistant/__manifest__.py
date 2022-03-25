# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Test Case For Bloopark by Agustin Wisky <agustinwisky@gmail.com>

{
    'name': "Search Assistant",
    'summary': """
        Search Product Assistant """,
    'description': """
        Custom search features for sales and purchase orders.
    """,
    'author': "Agustin Wisky <agustinwisky@gmail.com>",
    'website': "https://agustinwisky.com",
    'category': 'Proyect',
    'version': '13.0.1.0',
    'depends': [
        'purchase',
        'sale_stock',
        'product_brand',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/search_assistant_wizard_view.xml',
        'wizard/sale_assistant_wizard_view.xml',
        'wizard/purchase_assistant_wizard_view.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
}
