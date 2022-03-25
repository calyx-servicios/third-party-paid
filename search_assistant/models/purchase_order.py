from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    def call_purchase_search_assistant(self):
                
        return {    
            'name': _("Search Assistant"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'search.assistant',
            'context':{'active_model':'purchase.order'},
            'active_id': self.id,
            'target': 'new',
        }
        
    