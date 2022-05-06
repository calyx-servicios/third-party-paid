# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import itertools
import base64
import logging

_logger = logging.getLogger(__name__)


DISC_PERCENTAGE = ['prod_disc_percentage', 'prod_bxgy_percent', 'amount_percent']
DISC_AMOUNT = ['prod_disc_amount', 'prod_bxgy_amount', 'amount_disc_amount']
FIXED_PRICE = ['prod_fixed_price', 'prod_bxgy_fixed_price', 'amount_fixed_price']
GET_FREE = ['prod_bxgy_free', 'amount_get_free']


class ImportProductPromotion(models.TransientModel):
    """
    This wizard will confirm the all the selected draft invoices
    """

    _name = "import.product.promotion"
    _description = "Import Product Promotion"
    _rec_name = 'filename'

    data = fields.Binary('Import File', required=True)
    filename = fields.Char('File Name', required=True)

    def import_product(self):
        context = dict(self._context or {})
        BaseImport = self.env['base_import.import']
        active_id = context.get('active_id', False) or False
        promotion = self.env['pos.promotion'].browse(active_id)
        promotion_code = promotion.promotion_code
        row_number = 0
        if not active_id:
            raise UserError("Can't get Promotion")
        for record in self:
            if record.data:
                options = {}
                base_import = BaseImport.new()
                base_import.file = base64.b64decode(record.data)
                try:
                    rows = base_import._read_xls(options)
                    rows = itertools.islice(rows, 1, None)
                except Exception:
                    raise ValueError(_(
                        "Can't import this file, Please check it's format again or download a template above"))
                for row in rows:
                    row_number += 1
                    self.check_data(promotion_code, row, row_number)
                    self.process_data(row, active_id)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def check_float_number(self, float_num):
        try:
            float_num = float(float_num)
            return float_num
        except:
            return 0

    @api.model
    def check_data(self, promotion_code, row, row_number):
        promotion_free_qty = self.check_float_number(row[8]) or 0
        promotion_fixed_price = self.check_float_number(row[9]) or 0
        promotion_disc_percentage = self.check_float_number(row[10]) or 0
        promotion_disc_amount = self.check_float_number(row[11]) or 0
        print(">>>>> promotion_code:", promotion_code, promotion_free_qty,promotion_fixed_price,promotion_disc_percentage,promotion_disc_amount)
        if promotion_code in DISC_PERCENTAGE:
            if promotion_free_qty > 0 or promotion_fixed_price > 0 or promotion_disc_amount > 0:
                raise UserError("There is something wrong at row number: %s. The value of following fields should be equal to 0. But we have:"
                                "\n- Free Qty > 0, current value: %s."
                                "\n- Fixed Price > 0, current value: %s."
                                "\n- Disc. Amount > 0, current value: %s." %
                                (row_number, promotion_free_qty,
                                 promotion_fixed_price, promotion_disc_amount))
        if promotion_code in DISC_AMOUNT:
            if promotion_free_qty > 0 or promotion_fixed_price > 0 or promotion_disc_percentage > 0:
                raise UserError("There is something wrong at row number: %s. Please check following numbers if it's equal to 0 or not: "
                                "\n- Free Qty > 0, current value: %s."
                                "\n- Fixed Price > 0, current value: %s."
                                "\n- Disc. Percentage > 0, current value: %s." %
                                (row_number, promotion_free_qty,
                                 promotion_fixed_price,
                                 promotion_disc_percentage))
        if promotion_code in FIXED_PRICE:
            if promotion_free_qty > 0 or promotion_disc_percentage > 0 or promotion_disc_amount > 0:
                raise UserError("There is something wrong at row number: %s. The value of following fields should be equal to 0. But we have:"
                                "\n- Free Qty> 0, current value: %s"
                                "\n- Disc. Percentage > 0, current value: %s"
                                "\n- Disc. Amount > 0, current value: %s" %
                                (row_number, promotion_free_qty,
                                 promotion_disc_percentage,
                                 promotion_disc_amount))

        if promotion_code in GET_FREE:
            if promotion_fixed_price > 0 or promotion_disc_percentage > 0 or promotion_disc_amount > 0:
                raise UserError("There is something wrong at row number: %s. The value of following fields should be equal to 0. But we have:"
                                "\n- Fixed Price > 0, current value: %s"
                                "\n- Disc. Percentage > 0, current value: %s"
                                "\n- Disc. Amount > 0, current value: %s" %
                                (row_number, promotion_fixed_price,
                                 promotion_disc_percentage,
                                 promotion_disc_amount))


    @api.model
    def process_data(self, row, promotion_id):
        ProductEnv = self.env['product.product']
        PromotionProduct = self.env['pos.promotion.product']
        record_id = row[0] or False
        promotion_id = self._context.get('active_id', False)
        buy_product_name = row[1] or ''
        buy_product_ref = row[2] or ''
        buy_product_barcode = row[3] or ''
        buy_product_qty = self.check_float_number(row[4]) and row[4] or 0
        promotion_product_name = row[5] or ''
        promotion_product_ref = row[6] or ''
        promotion_product_barcode = row[7] or ''
        promotion_free_qty = self.check_float_number(row[8]) and row[8] or 0
        promotion_fixed_price = self.check_float_number(row[9]) and row[9] or 0
        promotion_disc_percentage = self.check_float_number(row[10]) and row[10] or 0
        promotion_disc_amount = self.check_float_number(row[11]) and row[11] or 0

        buy_product_id = False
        promotion_product_id = False
        product_domain = []
        if buy_product_name:
            product_domain.append(['name', '=', buy_product_name])
        if buy_product_ref:
            product_domain.append(['default_code', '=', buy_product_ref])
        if buy_product_barcode:
            product_domain.append(['barcode', '=', buy_product_barcode])
        if product_domain:
            buy_product = ProductEnv.search(product_domain, limit=1)
            buy_product_id = buy_product and buy_product.id or False

        # find promotion product domain
        promo_product_domain = []
        if promotion_product_name:
            promo_product_domain.append(['name', '=', promotion_product_name])
        if promotion_product_ref:
            promo_product_domain.append(['default_code', '=', promotion_product_ref])
        if promotion_product_barcode:
            promo_product_domain.append(['barcode', '=', promotion_product_barcode])

        if promo_product_domain:
            promotion_product = ProductEnv.search(promo_product_domain, limit=1)
            promotion_product_id = promotion_product and promotion_product.id or False

        if not buy_product_id and not promotion_product_id:
            _logger.warn("Can't find Buy product and Promotion product")
            return False
        vals = {
            'condition_product_id': buy_product_id,
            'condition_qty': buy_product_qty,
            'product_id': promotion_product_id,
            'free_qty': promotion_free_qty,
            'fixed_price': promotion_fixed_price,
            'disc_percentage': promotion_disc_percentage,
            'disc_amount': promotion_disc_amount,
        }
        domain = [('id', '=', record_id)]
        record = PromotionProduct.search(domain, limit=1)
        if record:
            if record.promotion_id.id != promotion_id:
                raise UserError(
                    "You're importing products of different promotion (name: '%s' - id: %s) "
                    "from current promotion (id: %s)" %
                    (record.promotion_id.name, record.promotion_id.id, promotion_id))
            record.write(vals)
        else:
            vals.update({
                'promotion_id': promotion_id
            })
            PromotionProduct.create(vals)