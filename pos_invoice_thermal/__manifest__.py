# -*- coding: utf-8 -*-
{
    'name':'Pos Invoice Thermal',
    'summary': 'Print Invoice to Thermal from POS',
    'description':'Print Invoice to Thermal from POS',
    'category': 'Point of Sale',
    'version':'0.5.1',
    'website':'https://globalresponse.cl',
    'author':'Daniel Santibáñez Polanco',
    'data': [
            'views/pos_invoice_thermal.xml',
            'views/pos_config.xml',
        ],
    'depends': [
                'point_of_sale',
                'print_to_thermal',
                'thermal_layouts',
            ],
    'application': True,
    'currency': 'EUR',
    'price': 50,
    'license': 'OPL-1',
}
