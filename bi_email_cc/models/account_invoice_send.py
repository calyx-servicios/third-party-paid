from odoo import fields, models, api
from ast import literal_eval


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    cc_partner_ids = fields.Many2many('res.partner', 'account_invoice_send_res_p_ids_rel','wizard_id', 'p_id', string='CC')
    bcc_partner_ids = fields.Many2many('res.partner', 'account_invoice_send_res_part_ids_rel','wizard_id', 'part_id', string='BCC')
    rply_partner_id = fields.Many2one('res.partner', string='Default Reply-To')
    is_cc = fields.Boolean(string='Enable CC')
    is_bcc = fields.Boolean(string='Enable BCC')
    is_reply = fields.Boolean(string='Enable Reply')

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceSend, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        rply_partner_id = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.rply_partner_id")
        cc_partner_ids = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.cc_partner_ids")
        bcc_partner_ids = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.bcc_partner_ids")
        is_cc = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.email_cc")
        is_bcc = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.email_bcc")
        is_reply = self.env["ir.config_parameter"].sudo().get_param("bi_email_cc.email_reply")
        if cc_partner_ids or bcc_partner_ids:
            res.update({
                'rply_partner_id': int(rply_partner_id),
                'cc_partner_ids': [(6, 0, literal_eval(cc_partner_ids))],
                'bcc_partner_ids': [(6, 0, literal_eval(bcc_partner_ids))],
                'is_cc': is_cc,
                'is_bcc': is_bcc,
                'is_reply': is_reply,
            })
        else:
            res.update({
				'rply_partner_id': int(rply_partner_id),
				'is_cc': is_cc,
				'is_bcc': is_bcc,
				'is_reply': is_reply,
			})
        return res

