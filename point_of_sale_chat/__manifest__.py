# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Kinfinity Tech Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    "name": "POS Chat",
    "summary": "Chat With POS.",
    "description": """
        This module will manage live chat option in POS.
    """,
    "version": "13.0.1.0.0",
    "category": "POS",
    "author": "Kinfinity Tech Pvt. Ltd.",
    "website": "https://www.kinfinitytech.com/",
    "application": True,
    "installable": True,
    "depends": [
        "point_of_sale",
        "mail",
        "mail_bot",
    ],
    'data': [
        'views/pos_config.xml',
        'views/template.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'images': [
        'static/description/banner.png'
    ],
    'price': 29,
    'license': 'OPL-1',
    'currency': 'EUR',
}
