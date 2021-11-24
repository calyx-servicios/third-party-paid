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

class upload_cart_rule(models.TransientModel):
    _name="upload.cart.rule"
    _description = 'Upload Cart Rule'
    
    prestashop_id=fields.Many2one('prestashop.instance','Prestashop Instance')
    
    # @api.one
    def upload_cart_rule(self,context=None,res_ids=None,presta_id=None): 
        if context==None:
            context=self._context
        else:
            context=context
#         print "srlf",self
        if res_ids and isinstance(res_ids,list):
            rec_list=res_ids
            presta_inst_id=presta_id
        else:
            active_ids=context.get('active_ids')
            rec_list=active_ids
            presta_inst_id=self.prestashop_id.id
#         active_ids=self._context.get('active_ids')
#         presta_inst_id=self.prestashop_id.id
        prestashop=self.env['sale.shop'].browse(presta_inst_id).presta_connect_json()
        prestashop.debug = True        
#         rec_list=active_ids
        for rec in rec_list:
            cart_obj=self.env['cart.rules'].browse(rec)
            cart_rule_schema=prestashop.get('cart_rules',options={'schema':'blank'})
            cart_rule_schema['cart_rule'].update({
                                               
                                               'date_from':cart_obj.date_from,
                                               'date_to': cart_obj.date_to, 
                                               'description': str(cart_obj.description), 
                                               'quantity': str(cart_obj.quantity), 
                                               'code': cart_obj.code, 
                                               'partial_use': str(int(cart_obj.partial_use)), 
                                               'id_lang': '1', 
                                               'minimum_amount':str(cart_obj.minimum_amount),
                                               'free_shipping': str(int(cart_obj.free_shipping)), 
                                               'active': str(int(cart_obj.prest_active)), 
                                               })
            if cart_obj.name:
                cart_rule_schema['cart_rule']['name']['language'].update({'value':cart_obj.name})

            if cart_obj.id_customer:
                customer_id=prestashop.search('customers',options={'filter[email]':cart_obj.id_customer.email})
                cart_rule_schema['cart_rule'].update({'id_customer': customer_id[0]}) 
            cart_id=prestashop.search('cart_rules',options={'filter[code]':cart_obj.code})
            if not cart_id :
                prestashop.add('cart_rules',cart_rule_schema)
            else:
                cart_rule_schema['cart_rule'].update({'id': cart_id[0]}) 
                prestashop.edit('cart_rules',cart_id[0],cart_rule_schema)
        return True
