# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    pricelist_id = fields.Many2one('product.pricelist')
    last_pay = fields.Float(
        string='Last Pay',
    )
    last_invoice_ids = fields.Char('Last Inovice ids')


    @api.model
    def create(self, vals):
        result = super(AccountInvoice, self).create(vals)
        x = lambda self:self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.user.company_id.id)), ('currency_id', '=', self.env.user.currency_id.id)], limit=1)
        vals['pricelist_id'] = x(self).id
        return result


    def _create_payment_transaction(self, vals):
        '''Similar to self.env['payment.transaction'].create(vals) but the values are filled with the
        current invoices fields (e.g. the partner or the currency).
        :param vals: The values to create a new payment.transaction.
        :return: The newly created payment.transaction record.
        '''
        # Ensure the currencies are the same.

        if self._context.get('multi_amount'):
            currency = self[0].currency_id
            if any([inv.currency_id != currency for inv in self]):
                raise ValidationError(_('A transaction can\'t be linked to invoices having different currencies.'))

            # Ensure the partner are the same.
            partner = self[0].partner_id
            if any([inv.partner_id != partner for inv in self]):
                raise ValidationError(_('A transaction can\'t be linked to invoices having different partners.'))

            # Try to retrieve the acquirer. However, fallback to the token's acquirer.
            acquirer_id = vals.get('acquirer_id')
            acquirer = None
            payment_token_id = vals.get('payment_token_id')

            if payment_token_id:
                payment_token = self.env['payment.token'].sudo().browse(payment_token_id)

                # Check payment_token/acquirer matching or take the acquirer from token
                if acquirer_id:
                    acquirer = self.env['payment.acquirer'].browse(acquirer_id)
                    if payment_token and payment_token.acquirer_id != acquirer:
                        raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
                        payment_token.acquirer_id.name, acquirer.name))
                    if payment_token and payment_token.partner_id != partner:
                        raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
                        payment_token.partner.name, partner.name))
                else:
                    acquirer = payment_token.acquirer_id

            # Check an acquirer is there.
            if not acquirer_id and not acquirer:
                raise ValidationError(_('A payment acquirer is required to create a transaction.'))

            if not acquirer:
                acquirer = self.env['payment.acquirer'].browse(acquirer_id)

            # Check a journal is set on acquirer.
            if not acquirer.journal_id:
                raise ValidationError(_('A journal must be specified of the acquirer %s.' % acquirer.name))

            if not acquirer_id and acquirer:
                vals['acquirer_id'] = acquirer.id

            string = self.last_invoice_ids.split(',')
            invoice_ids = self.env['account.move'].search([('name','in',string)])

            vals.update({
                'amount': self._context.get('multi_amount',0.0),
                'currency_id': currency.id,
                'partner_id': partner.id,
                'invoice_ids': [(6, 0, invoice_ids.ids)],
            })

            transaction = self.env['payment.transaction'].create(vals)

            # Process directly if payment_token
            if transaction.payment_token_id:
                transaction.s2s_do_transaction()

            return transaction
        elif self._context.get('amount'):
        
            currency = self[0].currency_id
            if any([inv.currency_id != currency for inv in self]):
                raise ValidationError(_('A transaction can\'t be linked to invoices having different currencies.'))

            # Ensure the partner are the same.
            partner = self[0].partner_id
            if any([inv.partner_id != partner for inv in self]):
                raise ValidationError(_('A transaction can\'t be linked to invoices having different partners.'))

            # Try to retrieve the acquirer. However, fallback to the token's acquirer.
            acquirer_id = vals.get('acquirer_id')
            acquirer = None
            payment_token_id = vals.get('payment_token_id')

            if payment_token_id:
                payment_token = self.env['payment.token'].sudo().browse(payment_token_id)

                # Check payment_token/acquirer matching or take the acquirer from token
                if acquirer_id:
                    acquirer = self.env['payment.acquirer'].browse(acquirer_id)
                    if payment_token and payment_token.acquirer_id != acquirer:
                        raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
                        payment_token.acquirer_id.name, acquirer.name))
                    if payment_token and payment_token.partner_id != partner:
                        raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
                        payment_token.partner.name, partner.name))
                else:
                    acquirer = payment_token.acquirer_id

            # Check an acquirer is there.
            if not acquirer_id and not acquirer:
                raise ValidationError(_('A payment acquirer is required to create a transaction.'))

            if not acquirer:
                acquirer = self.env['payment.acquirer'].browse(acquirer_id)

            # Check a journal is set on acquirer.
            if not acquirer.journal_id:
                raise ValidationError(_('A journal must be specified of the acquirer %s.' % acquirer.name))

            if not acquirer_id and acquirer:
                vals['acquirer_id'] = acquirer.id

            vals.update({
                'amount': self._context.get('amount',0.0),
                'currency_id': currency.id,
                'partner_id': partner.id,
                'invoice_ids': [(6, 0, self.ids)],
            })

            transaction = self.env['payment.transaction'].create(vals)

            # Process directly if payment_token
            if transaction.payment_token_id:
                transaction.s2s_do_transaction()

            return transaction
        else:
            return super(AccountInvoice, self)._create_payment_transaction(vals)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def render_invoice_button(self, invoice, submit_txt=None, render_values=None):
        if self._context.get('multi_amount'):
            values = {
                'partner_id': invoice.partner_id.id,
            }
            if render_values:
                values.update(render_values)
            return self.acquirer_id.with_context(submit_class='btn btn-primary', submit_txt=submit_txt or _('Pay Now')).sudo().render(
                self.reference,
                float(self._context.get('multi_amount',0.0)),
                invoice.currency_id.id,
                values=values,
            )
        elif self._context.get('amount'):
            values = {
                'partner_id': invoice.partner_id.id,
            }
            if render_values:
                values.update(render_values)
            return self.acquirer_id.with_context(submit_class='btn btn-primary', submit_txt=submit_txt or _('Pay Now')).sudo().render(
                self.reference,
                float(self._context.get('amount',0.0)),
                invoice.currency_id.id,
                values=values,
            )
        else:
            return super(PaymentTransaction, self).render_invoice_button(invoice, submit_txt=None, render_values=None)