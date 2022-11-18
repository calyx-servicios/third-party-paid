# -*- coding: utf-8 -*-
##############################################################################
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Producteca Odoo Connector',
    'version': '15.0.22.15',
    'author': 'Moldeo Interactive, Producteca',
    'website': 'https://www.moldeointeractive.com',
    "category": "Sales",
    "depends": ['base', 'product','sale_management','website_sale','stock','odoo_connector_api','delivery'],
    'data': [
        'security/odoo_connector_api_security.xml',
        'security/ir.model.access.csv',
        'views/company_view.xml',
    	#'views/posting_view.xml',
        #'views/product_post.xml',
        'views/connection_view.xml',
        'views/notification_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/invoice_view.xml',
        'views/wizards_view.xml',
        'views/stock_view.xml',
        'data/data.xml',
        'data/account_data.xml',
    	#'views/category_view.xml',
    	#'views/banner_view.xml',
        #'views/warning_view.xml',
        #'views/questions_view.xml',
        #'data/cron_jobs.xml',
        #'data/error_template_data.xml',
        #'data/parameters_data.xml',
	    #'report/report_shipment_view.xml',
        #'report/report_invoice_shipment_view.xml',
	    #'views/shipment_view.xml',
	    #'views/notifications_view.xml'
    ],
    'price': '350.00',
    'currency': 'USD',
    'images': [ 'static/description/main_screenshot.png',
                'static/description/producteca_screenshot.png',
                'static/description/producteca_ciclo_1.png',
                'static/description/producteca_configuration_1.png',
                'static/description/producteca_configuration_2.png',
                'static/description/producteca_configuration_3.png',
                'static/description/producteca_configuration_4.png',
                'static/description/moldeo_interactive_logo.png',
                'static/description/odoo_to_meli.png'],
    #"external_dependencies": {"python": ['pdf2image']},
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': True,
    'license': 'GPL-3',

}
