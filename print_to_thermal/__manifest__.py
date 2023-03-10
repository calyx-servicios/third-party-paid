# -*- coding: utf-8 -*-
{
    'name': 'Print to Thermal',
    'summary': 'Print Reports on Thermal Format from BackOffice',
    'description': 'Print Reports on Thermal Format from BackOffice',
    'category': 'sale',
    'version': '0.11.0',
    'website': 'https://globalresponse.cl',
    'author': 'Daniel Santibáñez Polanco',
    'data': [
            'views/print_to_thermal.xml',
            'views/res_config_settings.xml',
        ],
    'depends': [
                'web',
            ],
    'qweb':
        [
            'static/src/xml/widget.xml',
        ],

    'application': True,
    'currency': 'EUR',
    'price': 50,
    'license': 'OPL-1',
}
