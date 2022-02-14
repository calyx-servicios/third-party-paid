from odoo import models,fields,api


class prestashop_language(models.Model):
    _name='prestashop.language'
    
    presta_id = fields.Integer(string="Presta ID")
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    presta_instance_id = fields.Many2one('prestashop.instance', 'Instance')
        
        