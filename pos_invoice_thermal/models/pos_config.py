# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    thermal_invoice = fields.Boolean(
            string="Print all Invoices on thermal format",
            default=True,
        )