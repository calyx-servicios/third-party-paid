from odoo import tools
from odoo import api, fields, models
from odoo.tools.translate import _
import io
import base64
from base64 import b64decode
from StringIO import StringIO 
import requests
from lxml import etree
import xml.etree.ElementTree as ET

class upload_catalog_price(models.TransientModel):
    _name="upload.catalog.price"
    _description = 'Upload Catalog Price'
    
    prestashop_id=fields.Many2one('prestashop.instance','Prestashop Instance')
    
    # @api.one
    def upload_catalog_price(self): 
        active_ids=self._context.get('active_ids')
        presta_inst_id=self.prestashop_id.id
        prestashop=self.env['sale.shop'].browse(presta_inst_id).presta_connect_json()
        prestashop.debug = True        
        rec_list=active_ids
        for rec in rec_list:
            catlg_price_obj=self.env['catalog.price.rules'].browse(rec)
            specific_rule_schema=prestashop.get('specific_price_rules',options={'schema':'blank'})
            specific_rule_schema['specific_price_rule'].update({
                                               
                                               'from':catlg_price_obj.from_date,
                                               'to': catlg_price_obj.to_date, 
                                               'id_shop': '1', 
                                               'id_country': '0', 
                                               'id_group': '0', 
                                               'id_currency': '0', 
                                               'id_lang': '1', 
                                               'name':str(catlg_price_obj.name),
                                               'from_quantity': str(int(catlg_price_obj.from_quantity)), 
                                               'price': str(catlg_price_obj.price), 
                                               'reduction':str(catlg_price_obj.reduction),
                                               'reduction_type':str(catlg_price_obj.reduction_type),
                                               'reduction_tax':'0',
                                               })
#             if cart_obj.name:
#                 cart_rule_schema['cart_rule']['name']['language'].update({'value':cart_obj.name})
# 
#             if cart_obj.id_customer:
#                 customer_id=prestashop.search('customers',options={'filter[email]':cart_obj.id_customer.email})
#                 cart_rule_schema['cart_rule'].update({'id_customer': customer_id[0]}) 
            catlog_rule_id=prestashop.search('specific_price_rules',options={'filter[name]':catlg_price_obj.name})
            if not catlog_rule_id :
                prestashop.add('specific_price_rules',catlog_rule_id)
            else:
                specific_rule_schema['specific_price_rule'].update({'id': catlog_rule_id[0]}) 
                prestashop.edit('specific_price_rules',catlog_rule_id[0],specific_rule_schema)
        return True
