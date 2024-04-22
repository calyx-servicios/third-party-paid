# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    meli_id = fields.Char(unique=True, string=_('MercadoLibre ID'))
    meli_instance = fields.Many2one(comodel_name='melisync.settings', string=_('MercadoLibre Instance'))

    def meli_get_sales(self, settings_instance):
        """
            Get sales of MercadoLibre.
        """
        try:
            # Get meli instance client
            client = settings_instance.get_client_instance() # Get MELI and settings instance
            # Objects
            publications_obj = self.env['melisync.publications']
            publications_variants_relations_obj = self.env['melisync.publications.variants.relations']
            product_template_obj = self.env['product.template'] # Product template object
            res_partner_obj = self.env['res.partner'] # Res.partner object
            res_country_obj = self.env['res.country'] # Res.country object
            res_country_state_obj = self.env['res.country.state'] # Res.country.state object
            #l10n_latam_identification_type_obj = self.env['l10n_latam.identification.type'] # AFIP identification type
            #l10n_ar_afip_responsibility_type = self.env['l10n_ar.afip.responsibility.type'] # AFIP responsibility type
            # Complete data
            add_orders = []
            # Get date of search from.
            try:
                date_from = (datetime.now()-timedelta(days=settings_instance.last_days_orders_get))
            except:
                date_from = datetime.now()
            # Define get parameters
            params = {
                'order.date_created.from': date_from.strftime('%Y-%m-%dT00:00:00.000-00:00'),
                'order.status': 'paid',
                'seller': settings_instance.user_id,
            }
            # Get orders
            meli_orders = client.get_orders(params)
            # Loop orders
            for meli_order in meli_orders.get('results', []):
                # Variables
                order_lines = [] # Order lines
                meli_order_id = meli_order.get('id') # Meli Order ID
                # Get current order ID
                current_order_id = self.search([('meli_id', '=', meli_order_id)])
                # If exists, continue to the next order.
                if current_order_id:
                    continue
                try:
                    # Loop order items
                    for line in meli_order.get('order_items'):
                        # Parse product line
                        product = None
                        # Get item data (product data)
                        item_data = line.get('item')
                        item_id = item_data.get('id')
                        # Get item variant ID
                        variant_id = item_data.get('variation_id', False)
                        
                        # Parse product title
                        product_title = '{} ({})'.format(item_data.get('title'), item_id)

                        # Get variant ID
                        if variant_id:
                            product = publications_variants_relations_obj.search([('meli_id', '=', variant_id)]).variant_id
                        else:
                            # Get publication product main variant ID
                            # Search by publication template ID
                            publication = publications_obj.search([('publication_id', '=', item_id)])
                            product = publication.product_id.product_variant_id
                        
                        # If product not exists
                        if not product:
                            # Todo: check
                            product = product_template_obj.create({
                                'name': product_title,
                                'type': 'product',
                            }).product_variant_id
                        
                        # Add order line
                        order_line = (0, 0, {
                            'product_id': product.id,
                            'product_uom_qty': line.get('quantity'),
                            'name': product_title,
                            'price_unit': line.get('unit_price'),
                        })
                        order_lines.append(order_line)

                    billing_data = client.get_sale_billing_info(meli_order.get('id'))
                    # Get billing info object
                    billing_info = billing_data.get('billing_info')
                    # Get buyer data and check if exists in Odoo
                    buyer_id = meli_order.get('buyer').get('id')
                    # Get buyer partner ID
                    main_partner_id = res_partner_obj.search([('meli_id', '=', buyer_id)])
                    # If partner not registered
                    if not main_partner_id:
                        # Get buyer info
                        buyer_info = client.get_user(buyer_id)
                        buyer_country_id = res_country_obj.search([('code', '=', buyer_info.get('country_id', 'AR'))])
                        # Buyer data.
                        buyer_identification = buyer_info.get('identification', {})
                        buyer_company = buyer_info.get('company', {})
                        buyer_phone = buyer_info.get('phone', {})
                        buyer_address = buyer_info.get('address', {})
                        shipping_info = client.get_shipping(meli_order['shipping']['id'])
                        # Identification number and type
                        #buyer_identification_type = l10n_latam_identification_type_obj.search([('name', '=', buyer_identification.get('type'))])
                        # Parse buyer data
                        billing = billing_info['additional_info']

                        billing_user_data = {
                            'last_name': billing[0]['value'],
                            'doc_number': billing[1]['value'],
                            'doc_type': billing[2]['value'],
                            'zip_code': billing[3]['value'],
                            'street_name': billing[4]['value'],
                            'city_name': billing[5]['value'],
                            'state_name': billing[6]['value'],
                            'street_number': billing[7]['value'],
                            'site_id': billing[8]['value'],
                            'invoice_type': billing[9]['value'],
                            'state_code': billing[10]['value'],
                            'first_name': billing[11]['value'],
                            'taxpayer_type_id': billing[12]['value'],
                            'country_id': billing[13]['value'],
                        }

                        if 'Consumidor' in billing_user_data['taxpayer_type_id']:
                            name = f"{billing_user_data['first_name']} {billing_user_data['last_name']}"
                            
                            buyer_data = {
                                'company_type': 'person',
                                'meli_id': buyer_info.get('id'),
                                'name': name,
                                'country_id': buyer_country_id.id,
                                'city': billing_user_data['city_name'],
                                'zip':  billing_user_data['zip_code'],
                                'street': billing_user_data['street_name'],
                                'vat': billing_user_data['doc_number'],
                                'l10n_ar_afip_responsibility_type_id': 5,
                                'email': buyer_info.get('email', ''),
                                'phone': '{area_code} {number}'.format(area_code=buyer_phone.get('area_code', ''), number=buyer_phone.get('number', '')),
                            }
                        # Create the main partner
                        main_partner_id = res_partner_obj.create(buyer_data)
                    
                    #TODO: loop and repair
                    # Get order billing info to create INVOICE.
                    
                    # Get the invoice partner ID
                    # invoice_partner_id = res_partner_obj.search([('type', '=', 'invoice'), ('vat', '=', billing_info.get('doc_number'))])
                    # # If invoice partner not exists.
                    # if not invoice_partner_id:
                    #     billing_additional_info = {}
                    #     # Loop additional info keys/values.
                    #     for i in billing_info.get('additional_info'):
                    #         key, value = i.values()
                    #         # And save in dict
                    #         billing_additional_info[key] = value
                    #     # Get type of responsability (business or end consumer)
                    #     responsibility_name = billing_additional_info.get('TAXPAYER_TYPE_ID', 'Consumidor Final') # Consumidor Final is get of l10n_ar
                    #     # Get AFIP local data
                    #     #identification_type_id = l10n_latam_identification_type_obj.search([('name', '=', billing_info.get('doc_type'))])
                    #     #responsibility_type_id = l10n_ar_afip_responsibility_type.search([('name', '=', responsibility_name)])
                    #     # Get the state ID
                    #     state_id = res_country_state_obj.search([('country_id', '=', main_partner_id.country_id.id), ('name', '=', billing_additional_info.get('STATE_NAME'))])
                    #     if not state_id:
                    #         # Add the new state data
                    #         state_data = {
                    #             'code': 'Z-{}'.format(len(res_country_state_obj.search([]).ids)+1), # TODO: improve country-state-code
                    #             'country_id': main_partner_id.country_id.id,
                    #             'name': billing_additional_info.get('STATE_NAME'),
                    #         }
                    #         # Create the new state
                    #         state_id = res_country_state_obj.create(state_data)
                    #     # Search invoice partner or create
                    #     invoice_partner_data = {
                    #         'parent_id': main_partner_id.id, # Parent partner ID (invoice partner is children)
                    #         # Partner data
                    #         'company_type': 'person', # Type person
                    #         'type': 'invoice', # Address type
                    #         'name': '{} - {} ({})'.format(main_partner_id.name, billing_info.get('doc_number'), _('invoice')),
                    #         # Invoice AFIP data
                    #         #'l10n_latam_identification_type_id': identification_type_id.id, # Type of identification (CUIT/DNI)
                    #         'vat': billing_info.get('doc_number'), # Document number
                    #         # Address info
                    #         'country_id': main_partner_id.country_id.id, # Search ARGENTINA
                    #         'city': main_partner_id.city, # City
                    #         'state_id': state_id.id, # State
                    #         'zip': billing_additional_info.get('ZIP_CODE'),
                    #         'street': '{} {} - {}'.format(billing_additional_info.get('STREET_NAME'), billing_additional_info.get('STREET_NUMBER'), billing_additional_info.get('COMMENT')),
                    #         # Save fiscal data
                    #         'comment': _('Fiscal information: {} ({}: {})').format(responsibility_name, billing_info.get('doc_type'), billing_info.get('doc_number'))
                    #     }
                    #     # Create the invoice partner
                    #     invoice_partner_id = res_partner_obj.create(invoice_partner_data)
                    #     # Partner update data
                    #     update_data = {}
                    #     # If get the AFIP Data.
                    #     #if responsibility_type_id:
                    #     #    update_data['l10n_ar_afip_responsibility_type_id'] = responsibility_type_id.id, # AFIP Responsibility
                    #     # If is company to invoice
                    #     if billing_additional_info.get('BUSINESS_NAME'):
                    #         update_data['name'] = '{} ({})'.format(invoice_partner_data['name'], billing_additional_info.get('BUSINESS_NAME'))
                    #     # Update partner invoice data.
                    #     invoice_partner_id.write(update_data)
                    
                    # Loop order lines
                    order_data = {
                        'meli_id': meli_order_id,
                        'order_line': order_lines,
                        'partner_id': main_partner_id.id,
                        #'pricelist_id': meli_pricelist.id,
                        'partner_invoice_id': main_partner_id.id,
                        'partner_shipping_id': main_partner_id.id,
                        'meli_instance': settings_instance.id,
                        'company_id': settings_instance.company_id.id,
                        'warehouse_id': settings_instance.warehouse_id.id,
                        'picking_policy': settings_instance.picking_policy,
                    }
                    # Add order data to the orders list
                    add_orders.append(order_data)
                except Exception as e:
                    logger.warning(_('Cannot process order {}:\nError: {}'.format(meli_order.get('id'), e)))
            # Loop orders and save.
            for order in add_orders:
                try:
                    # Create order
                    order_id = self.create(order)
                    # Confirm
                    try:
                        order_id.action_confirm()
                    except Exception as e:
                        logger.warning(_('Cannot confirm order {}:\nError: {}'.format(order.get('meli_id'), e)))
                except Exception as e:
                    logger.warning(_('Cannot create order {}:\nError: {}'.format(order.get('meli_id'), e)))
        except Exception as e:
            logger.error('Error: {}'.format(e))
            raise UserError(_('Cannot get orders of MercadoLibre:\nError: {}'.format(e)))
