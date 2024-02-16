# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Product Brand',
    'version': '13.0.0.0.0',
    'category': 'Product',
    'summary': "Product Brand",
    'author': 'Agustin Wisky',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'product',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_view.xml',
        'views/sale_order_view.xml',
        'report/sale_report_templates.xml',
    ],
    'installable': True,
    'auto_install': False
}
