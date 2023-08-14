# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class GeneratePurchaseWiazrd(models.TransientModel):
	_name = "generate.purchase"
	_description = "Create Purchase Wizard"
	
	new_order_id = fields.Many2one('purchase.order', string="Quantity")

	def action_generate_po(self):
		inverse_approve = []
		res_id = self.env["purchase.order.line"].browse(self._context.get('active_ids',[]))
		res_obj = self.env['purchase.order'].sudo()
		for x in res_id:
			if x.state_id != 'confirm':
				raise UserError(('Please confirm purchase bid'))
			else:
				rep = res_obj.create({
						'partner_id':x.order_id.partner_id.id,
						'requisition_id':x.order_id.requisition_id.id,
						'origin':x.order_id.origin,
						'user_id':x.order_id.user_id.id,
						'order_line': [
								(0, 0, {
									'name':x.product_id.name,
									'product_id': x.product_id.id,
									'product_qty': x.product_qty,
									'date_planned':datetime.now(),
									'product_uom': x.product_uom[0].id,
									'price_unit': x.price_unit,
								})
							]
						})
				inverse_approve.append(x.order_id.requisition_id.id)	
		return {
			'name': 'Approved',
			'res_model': 'purchase.order',
			'type': 'ir.actions.act_window',
			'view_type':'form',
			'view_mode': 'tree,form',
			'domain': [('requisition_id','in',inverse_approve)],
		}
