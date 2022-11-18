# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, osv, models, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
import pdb
from .warning import warning
import requests
import json
from ast import literal_eval
from odoo.addons.odoo_connector_api.models.connection_notification import OcapiConnectionNotification

class ProductecaConnectionNotification(models.Model):

    _name = "producteca.notification"
    _description = "Producteca Notification"
    _inherit = "ocapi.connection.notification"

    #Connection reference defining mkt place credentials
    connection_account = fields.Many2one( "producteca.account", string="Producteca Account" )

    sale_order = fields.Many2one( "sale.order", related="producteca_sale_order.sale_order", string="Sale Order" )
    producteca_sale_order = fields.Many2one( "producteca.sale_order", string="Producteca Sale Order" )

    #def start_internal_notification(self, internals):
    #    noti = super( OcapiConnectionNotification, self).start_internal_notification( internals)
        #if noti:
        #    if not noti.producteca_sale_order:
        #       #search based on resource ids
    #    return noti


    def process_notification(self):
        result = []
        for noti in self:
            _logger.info("producteca process notification")
            if noti.connection_account:
                account = noti.connection_account
                if noti.topic == "sales" and noti.processing_logs:
                    #sales = json.loads(noti.processing_logs)
                    sales = literal_eval(noti.processing_logs)

                    _logger.info("Re Processing sales " + str(sales))

                    for sale in sales:
                        res = account.import_sale( sale, noti )
                        for r in res:
                            result.append(r)


                    _logger.info("process_notification " + str(result))
        return result
