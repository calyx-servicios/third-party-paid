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

class upload_category(models.TransientModel):
    _name="upload.category"
    _description = 'Upload Category'
    
    prestashop_id=fields.Many2one('prestashop.instance','Prestashop Instance')
    
    # @api.one
    def upload_category(self): 
        active_ids=self._context.get('active_ids')
        presta_inst_id=self.prestashop_id.id
        prestashop=self.env['sale.shop'].browse(presta_inst_id).presta_connect_json()
        prestashop.debug = True        
        rec_list=active_ids
        categ_list=[]
        for rec in rec_list:
            categ_rec=self.env['prestashop.category'].browse(rec)
            if categ_rec.presta_active:
                categ_list.append(categ_rec)
            
        self.env['prestashop.upload.products'].upload_categories(prestashop,categ_list)
        return True
