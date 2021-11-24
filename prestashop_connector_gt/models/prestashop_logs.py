from odoo import models, fields, api

class prestashop_log(models.Model):
    _name = 'prestashop.log'
    _order = 'log_date desc'
    
    # @api.model
    def create(self,vals):
        if not vals.get('log_name'):
            name = self.env['ir.sequence'].next_by_code('log.error')
            vals.update({
                'log_name': name
            })
        return super(prestashop_log, self).create(vals)
            
    
        

    log_name = fields.Char(string="Log Name", required=False, )
    log_date = fields.Datetime(string="Log Date",index=True,default=fields.Datetime.now)
    error_lines = fields.One2many("log.error", "log_id", string="Error lines", required=False, )
    all_operations = fields.Selection(string="Operations",
                                         selection=[('import_attributes', 'Import Prestashop attributes'),
                                                    ('import_categories', 'Import Prestashop categories'),
                                                    ('import_customers', 'Import Prestashop customers'),
                                                    ('import_suppliers', 'Import Prestashop suppliers'),
                                                    ('import_manufacturers', 'Import Prestashop manufacturers'),
                                                    ('import_addresses', 'Import Prestashop addresses'),
                                                    ('import_products', 'Import Prestashop products'),
                                                    ('import_inventory', 'Import Prestashop inventory'),
                                                    ('import_carriers', 'Import Prestashop carriers'),
                                                    ('import_orders', 'Import Prestashop orders'),
                                                    ('import_messages', 'Import Prestashop messages'),
                                                    ('import_cart_rules', 'Import Prestashop cart rules'),
                                                    ('import_catalog_rules', 'Import Prestashop catalog rules'),
                                                    ('import_country_state', 'Import Prestashop Country/State'),
                                                    ('update_categories', 'Update Prestashop categories'),
                                                    ('update_cart_rules', 'Update Prestashop cart rules'),
                                                    ('update_catalog_rules', 'Update Prestashop catalog rules'),
                                                    ('update_customers', 'Update Prestashop customers'),
                                                    ('update_product_data', 'Update Prestashop product data'),
                                                    ('update_inventory', 'Update Prestashop inventory'),
                                                    ('update_order_status', 'Update Prestashop orders'),
                                                    ('Export_customers', 'Export Prestashop customers'),
                                                    ('export_customer_message', 'Export Prestashop customer message'),
                                                    ('export_categories', 'Export Prestashop categories'),
                                                    ('export_product_data', 'Export Prestashop product data'),
                                                    ('export_order_status', 'Export Prestashop orders'),


                                                    ], )





class log_error(models.Model):
    _name = 'log.error'
    _rec_name = 'log_description'
    # _description = 'New Description'

    log_description = fields.Text(string="Log description")
    log_id = fields.Many2one("prestashop.log", string="Log description", required=False, )
    prestashop_id = fields.Char('Prestashop ID')
