from odoo import fields, models


class catolog_price_rules(models.Model):
    _name='catalog.price.rules'
    
    name=fields.Char('Name')
    from_quantity=fields.Integer('From Quantity')
    price=fields.Float('Price')
    reduction=fields.Float('Reduction')
    reduction_type=fields.Char('Reduction Type')
    from_date=fields.Datetime('From Date')
    to_date=fields.Datetime('To Date')
    shop_id=fields.Many2one('sale.shop','Shop ID')
    write_date = fields.Datetime(string="Write Date")
    presta_id = fields.Char('Presta ID')
    shop_ids = fields.Many2many('sale.shop', 'catalog_shop_rel', 'catalog_id', 'shop_id', string="Shop")