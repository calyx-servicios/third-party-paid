# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.osv import expression

import logging
logger = logging.getLogger(__name__)

class SiteIDsModel(models.Model):
    _name = 'melisync.site.ids'
    _description = 'MercadoLibreSync Site IDs Model'
    _rec_name = 'name'
    
    # Fields
    site_id = fields.Char(required=True, string=_('Site ID'))
    name = fields.Char(required=True, string=_('Name'))
    currency_id = fields.Char(required=True, string=_('Default Currency ID'))

    _sql_constraints = [
        ('site_id_unique', 'unique (site_id)', 'Site ID must be unique.'),
        ('name_unique', 'unique (name)', 'Name must be unique.'),
    ]

    @api.depends('site_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            name = '[{}] {}'.format(rec.site_id, rec.name)
            result.append((rec.id, name))
        return result

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
            Add search order by context.
        """
        ctx = self._context
        if 'order_display' in ctx:
            order = ctx['order_display']
        return super(SiteIDsModel, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def get_site_ids(self):
        """
            Get MercadoLibre Site IDs
        """
        # Objects
        melisync_settings_obj = self.env['melisync.settings']
        data = []
        try:
            client = melisync_settings_obj.get_client_instance_blank() # Get MercadoLibre instance
            # Get MercadoLibre site IDs
            data = client.get_sites()
            # Parse objects data.
            data = [{ 'site_id': site.get('id'), 'name': site.get('name'), 'currency_id': site.get('default_currency_id') } for site in data]
        except Exception as e:
            logger.error('Error on get site ids: {}'.format(e))
        return data

    def download_listing_types(self):
        # Objects
        melisync_listing_types_obj = self.env['melisync.listing.types']
        # Download listing types
        melisync_listing_types_obj.download(self)

    def download_shipping_methods(self):
        # Objects
        melisync_shipping_methods = self.env['melisync.shipping.methods']
        # Download listing types
        melisync_shipping_methods.download(self)

    @api.model    
    def download(self):
        try:
            # Get site ids of MercadoLibre
            site_ids = self.get_site_ids()
            logger.info('Downloaded {} site ids.'.format(len(site_ids)))
            # Loop sites
            for site in site_ids:
                try:
                    # Check if exists
                    site_id = self.search([('site_id', '=', site.get('site_id'))])
                    if not site_id:
                        # Create site
                        site_id = self.create(site)
                    # Download listing types
                    site_id.download_listing_types()
                    # Download shipping methods
                    site_id.download_shipping_methods()
                except Exception as e:
                    logger.warning('Error on create site_id "{}": {}'.format(site.get('site_id'), e))
        except Exception as e:
            raise UserError('Error on get site ids: {}'.format(e))

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        domain = expression.OR([[['name', operator, name]], [['site_id', operator, name]]])
        ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return [[x.id, x.display_name] for x in self.search([('id', 'in', ids)])]