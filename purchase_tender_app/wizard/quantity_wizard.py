# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class PurchaseWiazrd(models.TransientModel):
	_name = "purchase.wizard"
	_description = "Purchase Wizard"

	qty = fields.Integer(String="Quantity", required=True)

	def action_add_qty(self):
		self.ensure_one()
		order_line_id = self.env['purchase.order.line'].browse(self._context.get('active_ids'))
		order_line_id.product_qty = self.qty


	