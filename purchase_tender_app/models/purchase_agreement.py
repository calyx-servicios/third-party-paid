# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaserRequisition(models.Model):
	_inherit = 'purchase.requisition'

	def action_compare(self):
		self.ensure_one()
		return {
			'name': 'Bidline',
			'type': 'ir.actions.act_window',
			'view_mode': 'tree',
			'res_model': 'purchase.order.line',
			'domain': [('order_id.requisition_id','=',self.name)],
			'context': "{'search_default_hide_cancelled': 1, 'search_default_groupby_product': 1}"
		}

class PurchaserOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	state_id = fields.Selection([('confirm','Confirmed'),('new_cancel','Cancel')],string='State')

	def action_add_quantity(self):
		view = self.env.ref('purchase_tender_app.view_change_quantity_id')
		return {
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'purchase.wizard',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': False
			}

	def action_add_confirm(self):
		self.write({'state_id': 'confirm'})
		return

	def action_cancel(self):
		self.write({'state_id': 'new_cancel'})
		return