# -*- coding: utf-8 -*-
#############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import urllib
import base64
# import urllib.request
import json
import ast
import pytz
from odoo import api, fields, models, _
import socket
from datetime import timedelta, datetime, date, time
import time
from odoo import SUPERUSER_ID
#import mx.DateTime as dt
from odoo import netsvc
from odoo.tools.translate import _
from operator import itemgetter
from itertools import groupby
import json
import string, random
import binascii
import logging
import cgi
logger = logging.getLogger('__name__')

import logging

logger = logging.getLogger('stock')
from odoo.exceptions import UserError
import html2text

# try:
#     from urllib.request import urlopen
# except ImportError:
#     from urllib2 import urlopen


class SaleShop(models.Model):
	_inherit = "sale.shop"

	
	# @api.multi
	def import_prestashop_orders_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.import_orders()
		return True

	def import_prestashop_import_address_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.import_addresses()
		return True

	# @api.multi
	def import_prestashop_product_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.import_products()
		return True

	# @api.multi
	def import_prestashop_customer_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.import_customers()
		return True

	# @api.multi
	def import_prestashop_product_inventory_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.import_product_inventory()
		return True

	# @api.multi
	def prestashop_update_product_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.update_products()
		return True

	# @api.multi
	def prestashop_update_product_inventory_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.update_presta_product_inventory()
		return True

	# @api.multi
	def prestashop_product_export_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.export_presta_products()
		return True

	# @api.multi
	def pres_export_customer_scheduler(self, cron_mode=True):
		instance_obj = self.env['sale.shop']
		search_ids = self.search([])
		search_ids.export_presta_customers()
		return True

