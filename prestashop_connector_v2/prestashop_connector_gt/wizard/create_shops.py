from odoo import fields, models,api
from odoo.tools.translate import _
import xml.etree.ElementTree as ET
from odoo.exceptions import Warning

class CreatePrestashopShop(models.TransientModel):
    _name = "create.prestashop.shop"
    _description = "Create Prestashop Shop"
    
    def view_init(self,fields_list):
        if self._context is None:
            self._contex = {}
        res = super(CreatePrestashopShop, self).view_init(fields_list)
        active_ids = self._context.get('active_ids',[])
        if active_ids:
            search_shop = self.env['sale.shop'].search([('prestashop_instance_id','=',active_ids[0])])
            if search_shop:
                raise Warning( _('Shop Is Already Created'))
        return res
    
    # @api.one
    def create_prestashop_shop_action(self):
        data_prestashop_shops = self

        for data_prestashop_shop in data_prestashop_shops:
            code=(data_prestashop_shop.name)[0:6]
            shop_vals = {
                'name' : data_prestashop_shop.name,
                'code':code,
                'warehouse_id' : data_prestashop_shop.warehouse_id.id,
                'company_id' : data_prestashop_shop.company_id.id,
                'prestashop_instance_id' : self._context.get('active_id') and self._context['active_id'] or False,
                'prestashop_shop' : True,
            }
            prestashop_shop_id = self.env['sale.shop'].create(shop_vals)
            if prestashop_shop_id:
                message = _('%s Shop Successfully Created!')%(data_prestashop_shop['name'])
                self.env['sale.shop'].log(prestashop_shop_id.id, message)
                return {'type': 'ir.actions.act_window_close'}
            else:
                message = _('Error creating prestashop shop')
                self.log(message)
                return False
            
    def create_shops(self):
        active_id=self._context.get('active_id')
        presta_shop_obj = self.env['sale.shop']
        prestashop = presta_shop_obj.presta_connect()
        shops= prestashop.get('shops',1)
        shop=ET.tostring(shops)
            
        tags=shops.tag
            
        for shop in shops.findall('./shop'):
            id = shop.find('id').text
            name = shop.find('name').text
           
#         shop_config=prestashop.get('configurations',1)
#         print 'shop_config',shop_config
#         print  ET.tostring(shop_config)    
        return name
    
 
    name=fields.Char('Shop Name', size=64, required=True, default=lambda s:s.create_shops())
    warehouse_id=fields.Many2one('stock.warehouse', 'Warehouse',required=True)
    cust_address=fields.Many2one('res.partner', 'Address',)
    company_id=fields.Many2one('res.company', 'Company', required=False,default=lambda s: s.env['res.company']._company_default_get( 'stock.warehouse'))
    payment_default_id=fields.Many2one('account.payment.term', 'Default Payment Term', )
    picking_policy=fields.Selection([('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
        'Shipping Policy' ,
        help="""Pick 'Deliver each product when available' if you allow partial delivery.""")
    order_policy=fields.Selection([
            ('manual', 'On Demand'),
            ('picking', 'On Delivery Order'),
            ('prepaid', 'Before Delivery'),
        ], 'Create Invoice',
        help="""On demand: A draft invoice can be created from the sales order when needed. \nOn delivery order: A draft invoice can be created from the delivery order when the products have been delivered. \nBefore delivery: A draft invoice is created from the sales order and must be paid before the products can be delivered.""")
#        'picking_ids': fields.one2many('stock.picking.out', 'sale_id', 'Related Picking', readonly=True, help="This is a list of delivery orders that has been generated for this sales order."),
    invoice_quantity=fields.Selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on', help="The sale order will automatically create the invoice proposition (draft invoice). Ordered and delivered quantities may not be the same. You have to choose if you invoice based on ordered or shipped quantities. If the product is a service, shipped quantities means hours spent on the associated tasks.",)


# create_prestashop_shop()
