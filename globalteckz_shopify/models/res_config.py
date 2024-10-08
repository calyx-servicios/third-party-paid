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


from odoo import fields,models,api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_share_instance = fields.Boolean(
        'Share Shopify Instance to all companies',
        )


    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        instance_rule = self.env.ref('globalteckz_shopify.gt_shopify_instance_rule')
        res.update(
            company_share_instance=not bool(instance_rule.active),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        instance_rule = self.env.ref('globalteckz_shopify.gt_shopify_instance_rule')
        instance_rule.write({'active': not bool(self.company_share_instance)})
