# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    thermal_default_printer = fields.Char(
            string="Default Printer",
        )
    printer_urls = fields.Char(
            string="All available printers(separe with coma)",
        )
    time_alive_printer = fields.Integer(
            string="Time interval call to keep alive printer",
            default=5,
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        thermal_default_printer = ICPSudo.get_param('thermal.default_printer', '')
        thermal_printer_urls = ICPSudo.get_param('thermal.printer_urls', '')
        thermal_time_alive = int(ICPSudo.get_param('thermal.time_alive_printer', 5))
        res.update(
                thermal_default_printer=thermal_default_printer,
                printer_urls=thermal_printer_urls,
                time_alive_printer=thermal_time_alive
            )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('thermal.default_printer', self.thermal_default_printer)
        ICPSudo.set_param('thermal.printer_urls', self.printer_urls or '')
        ICPSudo.set_param('thermal.time_alive_printer', self.time_alive_printer)
