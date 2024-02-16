# -*- coding: utf-8 -*-
from odoo import models, _, api
from odoo.exceptions import UserError

import logging
logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    _inherit = 'res.currency'
    
    @api.model
    def meli_download(self):
        """
            Download MercadoLibre currencies
        """
        try:
            # Get MercadoLibre currency_id IDs
            currencies = self.get_currency_ids()
            # Loop currencies.
            for currency in currencies:
                try:
                    # Check if exists (active and inactive)
                    currency_id = self.search(['|', ('active', '=', True), ('active', '=', False), ('name', '=', currency.get('name'))])
                    # If not exists
                    if not currency_id:
                        # Create currency
                        currency_id = self.create(currency)
                    # Enable currency
                    currency_id.write({
                        'active': True,
                    })
                except Exception as e:
                    logger.warning('Error processing currency "{}": {}'.format(currency.get('name'), e))
                    pass
        except Exception as e:
            raise UserError('Error on get listing types: {}'.format(e))

    def get_currency_ids(self):
        """
            Get MercadoLibre Currency IDs
        """
        # Objects
        melisync_settings_obj = self.env['melisync.settings']
        data = []
        try:
            client = melisync_settings_obj.get_client_instance_blank() # Get MercadoLibre instance
            # Get MercadoLibre currency IDs
            data = client.get_currencies()
            """
                Response example: [{
                        "id": "ARS",
                        "symbol": "$",
                        "description": "Peso argentino",
                        "decimal_places": 2
                    },
                    ...
                ]
            """
            # Parse objects data.
            data = [{
                'name': currency.get('id'),
                'symbol': currency.get('symbol'),
                'currency_unit_label': currency.get('description'),
                'decimal_places': currency.get('decimal_places'),
                'position': 'before', # Symbol position
            } for currency in data]
        except Exception as e:
            logger.error('Error on get currency ids: {}'.format(e))
        return data