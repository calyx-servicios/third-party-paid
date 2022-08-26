# -*- coding: utf-8 -*-
from odoo import models, fields, _, api, modules, sql_db, http
from odoo.exceptions import UserError
import multiprocessing
import time
#from odoo.http import request

import logging
logger = logging.getLogger(__name__)

class Categories(models.Model):
    _name = 'melisync.categories'
    _description = 'MercadoLibre Categories Model'

    site_id = fields.Many2one(required=True, comodel_name='melisync.site.ids', string=_('Site ID'))
    categ_id = fields.Char(required=True, index=True, string=_('Category ID'))
    name = fields.Char(required=True, string=_('Name'))
    parent_id = fields.Char(required=False, string=_('Parent ID'))
    attribute_ids = fields.Many2many(comodel_name='product.attribute', string=_('Attribute IDs'))

    _sql_constraints = [
        ('categ_id_unique', 'unique (categ_id)', 'categ_id must be unique.')
    ]

    # Compute functions
    def _have_childrens(self):
        for rec in self:
            rec.have_childrens = len(rec.search([('parent_id', '=', self.categ_id)])) > 0

    # Compute functions
    def _get_parent_id(self):
        for rec in self:
            value = False
            if rec.parent_id:
                try:
                    value = self.search([('categ_id', '=', rec.parent_id)]).id
                except Exception as e:
                    logger.warning(_('Error getting parent_id for category "{}": {}'.format(rec.categ_id, e)))
            rec.parent_id_instance = value

    # Computed fields
    have_childrens = fields.Boolean(compute=_have_childrens, store=False, string=_('Have childrens'))
    parent_id_instance = fields.Many2one(compute=_get_parent_id, comodel_name='melisync.categories', string=_('Parent ID'))

    @api.depends('categ_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            name = '[{}] {}'.format(rec.categ_id, rec.name)
            result.append((rec.id, name))
        return result

    def sync_childrens(self):
        """
            Synchronize category childrens.
        """
        # Get MercadoLibre client instance
        client = self.env['melisync.settings'].get_client_instance(authenticate=False)
        try:
            # Get category site_id
            site_id = self.site_id.id
            # Get categories by site_id
            data = client.get_category_data(self.categ_id)
            # Loop childrens
            childrens = data.get('children_categories', [])
            # Loop childrens
            for category in childrens:
                try:
                    categ_id = self.search([('categ_id', '=', category.get('id'))])
                    if not categ_id:
                        categ_id = self.create({
                            'site_id': site_id,
                            'categ_id': category.get('id'),
                            'name': category.get('name'),
                            'parent_id': self.id,
                        })
                    categ_id.sync_childrens()
                except Exception as e:
                    logger.warning('Error on sync_childrens category "{}": {}'.format(category.get('name'), e))
        except Exception as e:
            logger.error('Error on get category "{}" childrens : {}'.format(self.categ_id, e))
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def sync_attributes(self, downloaded_attrs=None):
        """
            Synchronize category attributes.
        """
        # Objects
        product_attribute_obj = self.env['product.attribute']
        melisync_product_attribute_tags_obj = self.env['melisync.product.attribute.tags']
        # Objects
        product_attribute_value_obj = self.env['product.attribute.value']
        # Get MercadoLibre client instance
        client = self.env['melisync.settings'].get_client_instance(authenticate=False)
        try:
            # Get categories by site_id
            attributes = downloaded_attrs or client.get_category_attributes(self.categ_id)
            # Loop childrens
            for attr in attributes:
                try:
                    # Save attr value ids
                    attr_value_ids = []
                    # Check for existent attribute
                    attr_id = product_attribute_obj.search([('meli_id', '=', attr.get('id'))])
                    # If not exists
                    if not attr_id:
                        # Create attribute
                        attr_id = product_attribute_obj.create({
                            'meli_id': attr.get('id'),
                            'name': attr.get('name'),
                            'display_type': 'radio',
                            'create_variant': 'no_variant'
                        })
                    # Loop attribute tags
                    tags = attr.get('tags', {})
                    # List of tag ids to append to attr.
                    attr_tag_ids = []
                    for tag in tags:
                        try:
                            # Get the tag ID
                            tag_id = melisync_product_attribute_tags_obj.search([('name', '=', tag), ('value', '=', tags[tag])])
                            # If tag is not exists.
                            if not tag_id:
                                # Create tag
                                tag_id = melisync_product_attribute_tags_obj.create({
                                    'name': tag,
                                    'value': tags[tag],
                                })
                            attr_tag_ids.append(tag_id.id)
                        except Exception as e:
                            logger.warning('Error on process attribute tag "{}" for attribute "{}": {}'.format(tag, attr.get('id'), e))
                    # Add attribute tags to attribute.
                    attr_id.write({
                        'tag_ids': [(6, False, attr_tag_ids)],
                    })
                    # Add attribute to category.
                    self.write({
                        'attribute_ids': [(4, attr_id.id, False)],
                    })
                    # Loop attribute values
                    for index, value in enumerate(attr.get('values', [])):
                        try:
                            # Check for existent attribute value
                            value_id = product_attribute_value_obj.search([('meli_id', '=', value.get('id'))])
                            if not value_id:
                                value_id = product_attribute_value_obj.create({
                                    'meli_id': value.get('id'),
                                    'name': value.get('name'),
                                    'attribute_id': attr_id.id,
                                    'is_custom': False,
                                    'is_used_on_products': True,
                                    'sequence': index,
                                })
                            # Save value id.
                            attr_value_ids.append(value_id.id)
                        except Exception as e:
                            logger.warning('Error on create/edit attribute value "{}": {}'.format(value.get('id'), e))
                except Exception as e:
                    logger.warning('Error on parse attribute "{}" of category "{}": {}'.format(attributes.get('name'), self.categ_id, e))
        except Exception as e:
            logger.error('Error on get category "{}" attributes : {}'.format(self.categ_id, e))
        # Reload the view.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def view_childrens(self):
        """
            View childrens of category.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Subcategories'),
            'view_mode': 'tree,form',
            'res_model': 'melisync.categories',
            'domain': [('parent_id', '=', self.categ_id)],
        }

    def download_categories(self, settings_instance, withAttributes=False):
        """
            Download all categories of site ID.
            Parameters:
                - settings_instance: settings instance (melisync.settings).
                - withAttributes: get categories attributes
        """
        try:
            # Get MercadoLibre client instance
            client = settings_instance.get_client_instance(False)
            # Data
            site_id = settings_instance.site_id.site_id
            # Get all categories of this site.
            all_categories = client.get_all_categories(site_id, withAttributes=withAttributes)
            logger.info('Downloaded {} categories site {}.'.format(len(all_categories), site_id))
            # Loop categories
            categories_processed = []
            for key, value in all_categories.items():
                try:
                    # Parse category data.
                    categ_data = {
                        'site_id': settings_instance.site_id.id,
                        'categ_id': key,
                        'name': value.get('name'),
                    }
                    # If process attributes
                    if withAttributes:
                        categ_data['attributes'] = value.get('attributes', [])
                    try:
                        # Get category path_from_root
                        path_from_root = value.get('path_from_root')
                        # Get parent id (last item = this category)
                        categ_data['parent_id'] = path_from_root[-2].get('id')
                    except:
                        pass
                    # Add to list
                    categories_processed.append(categ_data)
                except Exception as e:
                    logger.warning('Error on process category_id "{}": {}'.format(key, e))
            # Start multiprocessing of categories.
            if settings_instance.multiprocess:
                # Get uid and database
                kwargs = { }
                # Get environment database
                try:
                    kwargs['uid'] = self.env.ref('base.user_root').id
                    kwargs['db'] = self.env.cr.dbname
                except:
                    kwargs['uid'] = request.uid
                    kwargs['db'] = request.db
                # Quantity of chunks
                chunks_qty = int(len(categories_processed)/settings_instance.multiprocess_qty_process)
                # Start categories process with multipricessing
                self.start_categories_create(categories_processed, chunks_qty, True, **kwargs)
            else:
                # Start categories process without multipricessing
                self.start_categories_create(categories_processed)
        except Exception as e:
            raise UserError('Error on sync all categories of Site "{}": {}'.format(site_id, e))

    def start_categories_create(self, categories, chunk_size=False, use_multiprocessing=False, **kwargs):
        """
            Start categories create with multi processing.
        """
        # Divide categories in chunks
        if chunk_size:
            chunks = [categories[x:x+chunk_size] for x in range(0, len(categories), chunk_size)]
        else:
            chunks = [categories]
        jobs = []
        # Loop chunks
        for index, chunk in enumerate(chunks):
            try:
                # If multiprocessing mode:
                if use_multiprocessing:
                    # Create multiprocessing instance
                    p = multiprocessing.Process(
                        target=self.start_categories_create_process, # Target function
                        args=(chunk, True, kwargs,), # Arguments
                        name='categories_chunk_{}'.format(index), # Name of process
                    )
                    p.daemon = True # Execute by daemon
                    jobs.append(p) # Save
                else:
                    # Normal mode
                    self.start_categories_create_process(chunk, False)
            except Exception as e:
                logger.warning('Error on processing categories chunk "{}": {}'.format(index, e))
        # Loop and start jobs.
        for job in jobs:
            job.start() # p.join() = Wait for process end

    def start_categories_create_process(self, categories, use_multiprocessing=False, kwargs=None):
        """
            Process categories.
            Arguments:
                - categories: list of categories.
                Example:
                [{
                    'site_id': 33, # ID for MLA
                    'categ_id': 'MLA845643',
                    'name': 'Category name',
                    'parent_id': 'MLA54312',
                    'attributes': [{...}, {...}, {...}],
                },]
        """
        start = time.time() # Get start time
        if use_multiprocessing:
            # Get current process data
            process = multiprocessing.current_process()
            processed = 0
            logger.info('Starting "{}" process with {} categories.'.format(process.name, len(categories)))
            try:
                # Connect to database
                db = sql_db.db_connect(kwargs.get('db'))
                # Get new connection to database and new cursor
                cr = db.cursor()
                #cr.autocommit(True) # Enable autocommit
                # Loop categories
                for index, value in enumerate(categories):
                    try:
                        # Check for existing category ID.
                        value['parent_id'] = value.get('parent_id', 'null')
                        # Generate query
                        query = """
                        INSERT INTO
                            melisync_categories
                        (
                            site_id,
                            categ_id,
                            name,
                            parent_id
                        ) VALUES (
                            {site_id},
                            '{categ_id}',
                            '{name}',
                            '{parent_id}'
                        ) ON CONFLICT (categ_id) DO NOTHING;
                        """.format(**value)
                        # Update
                        cr.execute(query)
                        processed += 1
                    except Exception as e:
                        logger.warning('Error on processing process "{}" index "{}" (Category {}).\nError: {}'.format(process.name, index, value.get('categ_id'), e))
                # Save transactions
                try:
                    #cr.execute("COMMIT;")
                    cr.commit()
                    cr.close()
                    #logger.info('Saved {}/{} categories with job of process: {}.'.format(processed, len(categories), process.name))
                except Exception as e:
                    logger.error('Error on close "{}" cursor: {}'.format(process.name, e))
                    #cr.rollback()
                    #raise
            except Exception as e:
                logger.error('Error on process {} for categories: {}'.format(process.name, e))
            logger.info('Finish "{}" process with {}/{} processed categories: {}s.'.format(process.name, processed, len(categories), time.time()-start))
        else:
            # Objects
            melisync_categories_obj = self.env['melisync.categories'] # Categories object
            logger.debug('Starting process categories without multiprocessing.')
            # Loop categories
            for index, value in enumerate(categories):
                try:
                    # Get category attributes
                    categ_attrs = value.pop('attributes', None)
                    # Check for existing category ID.
                    categ_id = melisync_categories_obj.search([('categ_id', '=', value.get('categ_id'))])
                    if not categ_id:
                        # Try create category
                        categ_id = melisync_categories_obj.create(value)
                        # Save categories attributes
                        if categ_attrs:
                            categ_id.sync_attributes(categ_attrs)
                except Exception as e:
                    logger.warning('Error on create category [{}]: {}'.format(value.get('categ_id'), e))
