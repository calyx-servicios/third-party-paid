# -*- coding: utf-8 -*-

from odoo.addons.web.controllers import main as report
from odoo.http import content_disposition, route, request, serialize_exception as _serialize_exception
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval
from werkzeug.urls import url_decode

import time
import json
import logging

_logger = logging.getLogger(__name__)


class ReportController(report.ReportController):

    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        # Trick the main reporter to think we want an HTML report
        new_converter = converter if converter != "thermal" else "html"
        response = super(ReportController, self).report_routes(
            reportname, docids, new_converter, **data)

        # If it was an XML report, just download the generated response
        if converter == "thermal":
            # XML header must be before any spaces, and it is a common error,
            # so let's fix that here and make developers happier
            response.data = response.data.strip()
            response.headers.set("Content-Type", "text/xml")
            response.headers.set('Content-length', len(response.data))
            response.headers.set(
                'Content-Disposition',
                content_disposition(reportname + ".xml"))
        return response

    @route()
    def report_download(self, data, token):
        """This function is used by 'qwebactionmanager.js' in order to trigger the download of
        a pdf/controller report.

        :param data: a javascript array JSON.stringified containg report internal url ([0]) and
        type [1]
        :returns: Response with a filetoken cookie and an attachment header
        """
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        try:
            if type == 'qweb-thermal':
                reportname = url.split('/report/thermal/')[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter='thermal')
                else:
                    # Particular report:
                    data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
                    response = self.report_routes(reportname, converter='thermal', **dict(data))
                response.set_cookie('fileToken', token)
                return response
            else:
                return super(ReportController, self).report_download(data, token)
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

    @route('/web/report/thermal/params', type='json', auth='user', website=False)
    def thermal_params(self):
        config = request.env['ir.config_parameter'].sudo()
        return {
            'thermal.default_printer': config.get_param('thermal.default_printer'),
            'thermal.printer_urls': config.get_param('thermal.printer_urls'),
            'thermal.time_alive_printer': config.get_param('thermal.time_alive_printer')
        }
