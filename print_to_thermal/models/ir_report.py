# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree

import logging

_logger = logging.getLogger(__name__)


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(selection_add=[
            ("qweb-thermal", "Thermal Format")], ondelete={'qweb-thermal': 'set default'})

    @api.model
    def _get_report_from_name(self, report_name):
        res = super(ReportAction, self)._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env['ir.actions.report']
        qwebtypes = ['qweb-thermal']
        conditions = [('report_type', 'in', qwebtypes),
                      ('report_name', '=', report_name)]
        context = self.env['res.users'].context_get()
        return report_obj.with_context(context).search(conditions, limit=1)

    @api.model
    def render_qweb_thermal(self, docids, data):
        result = self.render_qweb_html(docids, data=data)
        return etree.tostring(
            etree.fromstring(
                str(result[0], 'UTF-8').lstrip('\n').lstrip().encode('UTF-8')
            ),
            encoding='UTF-8',
            xml_declaration=True,
            pretty_print=True
    ), "xml"
