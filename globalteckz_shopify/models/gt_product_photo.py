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


class GtProductPhoto(models.Model):
    _name = 'gt.product.photo'
    _description = 'Product photo'
    

    color = fields.Char(string='Color')
    gt_image= fields.Binary('Image')
    gt_product_id = fields.Many2one('product.product', 'Product ID')
    gt_image_src= fields.Char('Image Source')
    gt_is_exported=fields.Boolean('Exported')
    gt_image_position = fields.Integer('Image Position',)
    gt_image_id=fields.Char('Shopify Image ID', attachment=True)
    gt_product_temp_id = fields.Many2one('product.template', string='Product Template ID ')
    gt_shopify_instance_id = fields.Many2one('gt.shopify.instance', string='Shopify Instance')
    gt_image_name = fields.Char(string='Image Name')
    
    
GtProductPhoto()