from odoo import fields , models , api , _
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"

	cc_partner_ids = fields.Many2many('res.partner',  'company_id', string="Default CC")
	bcc_partner_ids = fields.Many2many('res.partner', string="Default BCC")
	email_cc = fields.Boolean(string='Enable Email CC')
	email_bcc = fields.Boolean(string='Enable Email BCC')
	email_reply = fields.Boolean(string='Enable Reply-To')
	rply_partner_id = fields.Many2one('res.partner',string='Default Reply-To')
	email = fields.Char(string="Email")
	
	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		email_cc = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.email_cc")
		email_bcc = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.email_bcc")
		email_reply = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.email_reply")
		cc_partner_ids = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.cc_partner_ids")
		bcc_partner_ids = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.bcc_partner_ids")
		rply_partner_id = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.rply_partner_id")
		res.update(
			email_cc = email_cc,
			email_bcc = email_bcc,
			email_reply = email_reply,
			cc_partner_ids = [(6,0 ,literal_eval(str(cc_partner_ids)))] if cc_partner_ids else False,
			bcc_partner_ids = [(6,0 ,literal_eval(str(bcc_partner_ids)))] if bcc_partner_ids else False,
			rply_partner_id = int(rply_partner_id),
		)
		return res

	def set_values(self):
		res = super(ResConfigSettings, self).set_values()
		config_env = self.env['ir.config_parameter'].sudo()
		config_env.set_param("bi_email_cc.email_cc", self.email_cc)
		config_env.set_param("bi_email_cc.email_bcc", self.email_bcc)
		config_env.set_param("bi_email_cc.email_reply", self.email_reply)
		config_env.set_param("bi_email_cc.cc_partner_ids", self.cc_partner_ids.ids)
		config_env.set_param("bi_email_cc.bcc_partner_ids", self.bcc_partner_ids.ids)
		config_env.set_param("bi_email_cc.rply_partner_id", int(self.rply_partner_id.id))

