# -*- coding: utf-8 -*-
#############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _

class account_invoice(models.Model):
    _inherit = "account.move"
                
    is_prestashop=fields.Boolean('Prestashop')
    total_discount_tax_excl=fields.Float('Discount(tax excl.)')
    total_discount_tax_incl=fields.Float('Discount(tax incl)')
    total_paid_tax_excl= fields.Float('Paid (tax excl.)')
    total_paid_tax_incl=fields.Float('Paid (tax incl.)')
    total_products_wt=fields.Float('Weight')
    total_shipping_tax_excl=fields.Float('Shipping(tax excl.)')
    total_shipping_tax_incl=fields.Float('Shipping(tax incl.)')
    total_wrapping_tax_excl=fields.Float('Wrapping(tax excl.)')
    total_wrapping_tax_incl=fields.Float('Wrapping(tax incl.)')
    shop_ids = fields.Many2many('sale.shop', 'invoice_shop_rel', 'invoice_id', 'shop_id', string="Shop")

    def invoice_pay_customer_base(self):
        accountinvoice_link = self
        journal_id = self._default_journal()

        if self.type == 'out_invoice':
            self.with_context(type='out_invoice')
        elif self.type == 'out_refund':    
            self.with_context(type='out_refund')
        self.pay_and_reconcile(journal_id,accountinvoice_link.amount_total, False, False)
        return True    
    
account_invoice()

