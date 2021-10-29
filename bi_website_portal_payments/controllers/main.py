# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import json
from odoo import http, _
from odoo.exceptions import ValidationError, UserError, AccessError, MissingError
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, date
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.osv import expression
from odoo.tools import consteq, float_round
import pprint
from odoo.addons.portal.controllers.portal import _build_url_w_params

def _partner_format_address(address1=False, address2=False):
    return ' '.join((address1 or '', address2 or '')).strip()

def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]

class website_account_payment(CustomerPortal):

    @http.route(['/my/invoices/multiple/payment'], type='http', auth="public", website=True)
    def multiple_payment(self,access_token=None,**post):
        if post:
            invoice_ids = request.env['account.move']

            if post.get('invoice_ids') == None:
                return request.redirect('/my/invoices/multiple/payment')

            invoices = []
            id_list = post['invoice_ids']            
            new_list = id_list.split(',')

            if id_list != '':
                for invoice in new_list:
                    try:
                        invoice_sudo = self._document_check_access('account.move', int(invoice), access_token)
                    except (AccessError, MissingError):
                        return request.redirect('/my')

                    invoice_ids += invoice_sudo

                values = self._invoice_get_page_view_values(invoice_ids[0], access_token, **post)
                    
                acquirers = values.get('acquirers')

                if not acquirers:
                    domain = expression.AND([
                        ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', invoice_ids[0].company_id.id)],
                        ['|', ('country_ids', '=', False), ('country_ids', 'in', [invoice_ids[0].partner_id.country_id.id])]
                    ])
                    acquirers = request.env['payment.acquirer'].sudo().search(domain)

                    values.update({
                        'acquirers' : acquirers
                    })

                pms = values.get('pms')
                if not pms:
                    pms = request.env['payment.token']
                    values.update({
                        'pms' : pms
                    })

                if acquirers:
                    country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
                    values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id)

                PaymentProcessing.remove_payment_transaction(invoice_ids[0].transaction_ids)
                values.update({
                    'invoices' : invoice_ids,
                    'invoice' : invoice_ids[0],
                    'invoice_num' : ', '.join(invoice_ids.mapped('name')),
                    'total_amount' : sum(invoice.amount_residual_signed for invoice in invoice_ids),
                })

                return request.render("bi_website_portal_payments.pay_multiple_payment",values)
            else:
                return request.render("bi_website_portal_payments.pay_multiple_payment")


    @http.route(['/my/invoices/transaction/multi/<string:invoice_id>'], type='json', auth='public')
    def multi_partial_transaction(self, acquirer_id, invoice_id, save_token=False, access_token=None, **kwargs):
        invoice_sudo = request.env['account.move'].sudo().browse(int(invoice_id))
        if not invoice_sudo:
            return False

        try:
            acquirer_id = int(acquirer_id)
        except:
            return False

        if request.env.user._is_public():
            save_token = False # we avoid to create a token for the public user

        success_url = kwargs.get(
            'success_url', "%s?%s" % (invoice_sudo.access_url, url_encode({'access_token': access_token}) if access_token else '')
        )
        vals = {
            'acquirer_id': acquirer_id,
            'return_url': success_url,
        }

        if save_token:
            vals['type'] = 'form_save'


        transaction = invoice_sudo.with_context(multi_amount=invoice_sudo.last_pay)._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(transaction)

        return transaction.with_context(multi_amount=invoice_sudo.last_pay).render_invoice_button(
            invoice_sudo,
            submit_txt=_('Pay & Confirm'),
            render_values={
                'type': 'form_save' if save_token else 'form',
                'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
            }
        )


    @http.route(['/my/invoices/token/multi/<string:invoice_id>'], type='http', auth='public', website=True)
    def multi_partial_payment_token(self, pm_id, invoice_id, return_url=None, **kwargs):
        """ Use a token to perform a s2s transaction """
        error_url = kwargs.get('error_url', '/my')
        access_token = kwargs.get('access_token')
        params = {}
        if access_token:
            params['access_token'] = access_token

        invoice_sudo = request.env['account.move'].sudo().browse(int(invoice_id)).exists()
        if not invoice_sudo:
            params['error'] = 'pay_invoice_invalid_doc'
            return request.redirect(_build_url_w_params(error_url, params))

        success_url = kwargs.get(
            'success_url', "%s?%s" % (invoice_sudo.access_url, url_encode({'access_token': access_token}) if access_token else '')
        )
        try:
            token = request.env['payment.token'].sudo().browse(int(pm_id))
        except (ValueError, TypeError):
            token = False
        token_owner = invoice_sudo.partner_id if request.env.user._is_public() else request.env.user.partner_id
        if not token or token.partner_id != token_owner:
            params['error'] = 'pay_invoice_invalid_token'
            return request.redirect(_build_url_w_params(error_url, params))

        vals = {
            'payment_token_id': token.id,
            'type': 'server2server',
            'return_url': _build_url_w_params(success_url, params),
        }

        tx = invoice_sudo.with_context(multi_amount=invoice_sudo.last_pay)._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(tx)

        params['success'] = 'pay_invoice'
        return request.redirect('/payment/process')


    @http.route(['/my/invoices/partial/<int:invoice_id>'], type='http', auth="public", website=True)
    def pay_partial(self, invoice_id, access_token=None,**post):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **post)

        acquirers = values.get('acquirers')
        if not acquirers:
            domain = expression.AND([
                ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', invoice_sudo.company_id.id)],
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [invoice_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values.update({
                'acquirers' : acquirers
            })

        pms = values.get('pms')
        if not pms:
            pms = request.env['payment.token']
            values.update({
                'pms' : pms
            })

        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id)

        return request.render("bi_website_portal_payments.pay_portal_payment",values)


    @http.route(['/my/invoices/transaction/<string:invoice_id>'], type='json', auth='public')
    def partial_transaction(self, acquirer_id, invoice_id, save_token=False, access_token=None, **kwargs):
        invoice_sudo = request.env['account.move'].sudo().browse(int(invoice_id))
        if not invoice_sudo:
            return False

        try:
            acquirer_id = int(acquirer_id)
        except:
            return False

        if request.env.user._is_public():
            save_token = False # we avoid to create a token for the public user

        success_url = kwargs.get(
            'success_url', "%s?%s" % (invoice_sudo.access_url, url_encode({'access_token': access_token}) if access_token else '')
        )
        vals = {
            'acquirer_id': acquirer_id,
            'return_url': success_url,
        }

        if save_token:
            vals['type'] = 'form_save'

        transaction = invoice_sudo.with_context(amount=invoice_sudo.last_pay)._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(transaction)

        return transaction.with_context(amount=invoice_sudo.last_pay).render_invoice_button(
            invoice_sudo,
            submit_txt=_('Pay & Confirm'),
            render_values={
                'type': 'form_save' if save_token else 'form',
                'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
            }
        )


    @http.route(['/my/invoices/token/<string:invoice_id>'], type='http', auth='public', website=True)
    def partial_payment_token(self, pm_id, invoice_id, return_url=None, **kwargs):
        """ Use a token to perform a s2s transaction """
        error_url = kwargs.get('error_url', '/my')
        access_token = kwargs.get('access_token')
        params = {}
        if access_token:
            params['access_token'] = access_token

        invoice_sudo = request.env['account.move'].sudo().browse(int(invoice_id)).exists()
        if not invoice_sudo:
            params['error'] = 'pay_invoice_invalid_doc'
            return request.redirect(_build_url_w_params(error_url, params))

        success_url = kwargs.get(
            'success_url', "%s?%s" % (invoice_sudo.access_url, url_encode({'access_token': access_token}) if access_token else '')
        )
        try:
            token = request.env['payment.token'].sudo().browse(int(pm_id))
        except (ValueError, TypeError):
            token = False
        token_owner = invoice_sudo.partner_id if request.env.user._is_public() else request.env.user.partner_id
        if not token or token.partner_id != token_owner:
            params['error'] = 'pay_invoice_invalid_token'
            return request.redirect(_build_url_w_params(error_url, params))

        vals = {
            'payment_token_id': token.id,
            'type': 'server2server',
            'return_url': _build_url_w_params(success_url, params),
        }

        tx = invoice_sudo.with_context(amount=invoice_sudo.last_pay)._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(tx)

        params['success'] = 'pay_invoice'
        return request.redirect('/payment/process')


class GenerateInovices(http.Controller):

    @http.route('/inovice/amount', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def last_inv_amount(self, **post):
        if post.get('invoice_id'):
            invoice_sudo = request.env['account.move'].sudo().browse(int(post.get('invoice_id'))).exists()
            invoice_sudo.write({
                'last_pay' : float(post.get('amount1',0.0))
            })
        return json.dumps({'data' : True})

    @http.route('/inovices/amount', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def multiple_inv_amount(self, **post):
        if post.get('invoice_num'):
            names =  post.get('invoice_num').split(', ')
            invoice_ids = request.env['account.move'].sudo().search([('name','in',names)])
            invoice_sudo = request.env['account.move'].sudo().browse(int(post.get('invoice'))).exists()
            invoice_sudo.write({
                'last_pay' : float(post.get('amount',0.0)),
                'last_invoice_ids' : ','.join((invoice_ids.mapped('name')))
            })
            return json.dumps({'data' : True})
        else:
            return json.dumps({'data' : False})