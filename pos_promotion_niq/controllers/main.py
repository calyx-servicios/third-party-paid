# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import ExportXlsxWriter
from odoo import http


class Controller(http.Controller):


    @http.route(['/pos_promotion_niq/product/export'], type='http', auth="user")
    def index(self, promotion_id):
        promotion_id = int(promotion_id)
        promotion = request.env['pos.promotion'].sudo().browse(promotion_id)
        columns_headers, promotion_data = promotion.web_export_promotion_product()

        return request.make_response(
            self.export_from_data(columns_headers, promotion_data),
            headers=[
                ('Content-Disposition', content_disposition('promotion_product.xls')),
                ('Content-Type', 'application/vnd.ms-excel')
            ],
            cookies={})

    def export_from_data(self, fields, rows):
        with ExportXlsxWriter(fields, len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)

        return xlsx_writer.value