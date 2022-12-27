from odoo import api, fields, models, _
from datetime import timedelta, datetime
from odoo import netsvc
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


from odoo import api, models


class GtMagentoStore(models.Model):
    _inherit = "gt.magento.store"
    _description = 'Magento Store'
    
    def Import_orderses_scheduler(self, cron_mode=True):
        store_obj = self.env['gt.magento.store']
        store_id = store_obj.search([])
        for stores in store_id:
            stores.GtCreateMagentoOrders()
        return True
        
        
       
    def Update_stock_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        for instance in  instance_id:
            instance.GtExportProductStock()
        return True
    
    
    def Import_product_stock_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        instance_id.GtImportMagentoStock()
        return True
        
     
    def Update_product_scheduler(self, cron_mode=True):
        products = self.env['product.template'].search([])
        products.GtUpdateMagentoProductTemplate()
   
    
    def Import_product_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        for instance in  instance_id:
            instance.GtImportMagentoProduct()
        return True
    
    
    def Import_product_image_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        for instance in  instance_id:
            instance.GtImportProductImage()
        return True
    

    
    def Import_product_attributes_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        instance_id.GtCreateMagentoAttributes()
        return True    
    
    
    def Import_product_attributes_set_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        instance_id.GtCreateMagentoAttributeSet()
        return True   
        
    
    def Import_product_categories_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        instance_id.GtImportMagentoCategories()
        return True   
    
    
    def Export_product_categories_scheduler(self, cron_mode=True):
        instance_obj = self.env['gt.magento.instance']
        instance_id = instance_obj.search([])
        instance_id.ExportMultipleMagentoCategories()
        return True   
    
    

        
        
        
