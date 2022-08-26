# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError

import logging
logger = logging.getLogger(__name__)

class ListingTypesModel(models.Model):
    _name = 'melisync.listing.types'
    _description = 'MercadoLibre Listing Types Model'
    _rec_name = 'field_name'

    site_id = fields.Many2one(required=True, comodel_name='melisync.site.ids', string=_('Site ID'))
    listing_id = fields.Char(required=True, string=_('Listing ID'))
    name = fields.Char(required=True, string=_('Name'))

    _sql_constraints = [
        ('listing_unique', 'unique (site_id, listing_id)', 'listing_type must be unique.')
    ]

    # Computed methods
    def _field_name_get(self):
        for rec in self:
            rec.field_name = '{} ({})'.format(rec.name, rec.listing_id)

    # Computed fields
    field_name = fields.Char(compute=_field_name_get, store=False, string=_('Field name'))
    
    @api.model
    def download(self, site_id):
        """
            Download MercadoLibre listing types for Site
        """
        # Objects
        melisync_settings_obj = self.env['melisync.settings']
        try:
            # Get meli instance
            client = melisync_settings_obj.get_client_instance_blank() # Get MercadoLibre instance
            # Get MercadoLibre listing_type IDs
            listing_type_ids = client.get_listing_types(site_id.site_id)
            logger.info('Downloaded {} listing types for site {}.'.format(len(listing_type_ids), site_id.site_id))
            # Loop listing types.
            for listing_type in listing_type_ids:
                # Change key name
                listing_type['listing_id'] = listing_type.pop('id')
                listing_type['site_id'] = site_id.id
                try:
                    # Check if exists
                    listing_type_id = self.search([('site_id', '=', listing_type.get('site_id')), ('listing_id', '=', listing_type.get('listing_id'))])
                    # If not exists
                    if not listing_type_id:
                        # Create listing_type
                        self.create(listing_type)
                except Exception as e:
                    logger.warning('Error processing listing_type for site_id "{}": {}'.format(site_id.site_id, e))
                    pass
        except Exception as e:
            raise UserError('Error on get listing types: {}'.format(e))