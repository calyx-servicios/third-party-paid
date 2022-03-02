# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#    Globalteckz                                                              #
#    Copyright (C) 2013-Today Globalteckz (http://www.globalteckz.com)        #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU Affero General Public License as           #
#    published by the Free Software Foundation, either version 3 of the       #
#    License, or (at your option) any later version.                          #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU Affero General Public License for more details.                      #
#                                                                             #
#    You should have received a copy of the GNU Affero General Public License #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #   
###############################################################################

from odoo import fields,models

class ProductPhoto(models.Model):
    _name = 'product.photo'
    _description = 'Product photo'
    
    product_id = fields.Many2one('product.product', 'Product')
    name= fields.Char('Name')
    description= fields.Text('Description')
    image_alt= fields.Text('Image Label')
    image= fields.Binary('Image')
    is_exported=fields.Boolean('Exported')
    link=fields.Boolean('Link')
    magento_url=fields.Char('magento Url')
    url=fields.Char('URL')
    base_image = fields.Boolean(string='Base Image')
    small_image = fields.Boolean('Small Image')
    thumbnail = fields.Boolean('Thumbnail Image')
    swatch_image = fields.Boolean(string='Swatch Image')
    position = fields.Integer('Magento Position',)
    magento_id=fields.Char('Magento ID')
    image_extension = fields.Selection([('png', 'PNG'),('jpeg', 'JPEG')],'Image Extension Type')
    #product_mag_id = fields.Many2one('product.template','Product')
    magento_instance_ids = fields.Many2many('gt.magento.instance','mage_image_rel','img_insta_id','pimgo_id','Magento Instance')
    gt_magento_image_ids = fields.Many2many('gt.magento.product.image.multi', 'img_product_rel', 'img_id', 'imss_id', string='Product ID')
    
    

class GtMagentoProductImageMulti(models.Model):
    _name = 'gt.magento.product.image.multi'
    _rec_name = 'magento_id'
    _description = 'Magento Image Multi ID'
    
    images_ids = fields.Many2one('product.photo', string="Image")
    magento_id = fields.Char(string='Product ID')
    gt_magento_instance_id = fields.Many2one('gt.magento.instance', string='Shopify Instance')
    gt_magento_exported = fields.Boolean(string='Shopify Exported')
    