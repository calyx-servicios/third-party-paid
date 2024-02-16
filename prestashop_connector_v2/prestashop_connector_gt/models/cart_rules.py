from odoo import fields, models


class cart_rules(models.Model):
    _name='cart.rules'
    
    name=fields.Char('Name')
    id_customer=fields.Many2one('res.partner','Customer')
    date_from=fields.Datetime('Date From')
    date_to=fields.Datetime('Date To')
    quantity=fields.Integer('Quantity')
    code=fields.Char('Code')
    minimum_amount =fields.Float('Minimum Amount')
    free_shipping=fields.Boolean('Free Shipping')
    partial_use=fields.Boolean('Partial Use')
    prest_active=fields.Boolean('Active')
    description=fields.Text('Description')
    prestashop_id=fields.Many2one('sale.shop')
    presta_id = fields.Char('Presta ID')
    write_date = fields.Datetime(string="Write Date")
    shop_ids = fields.Many2many('sale.shop', 'cart_shop_rel', 'cart_id', 'shop_id', string="Shop")

    shop_id = fields.Many2one('sale.shop', 'Shop ID')
cart_rules()   
    
    
    
    
