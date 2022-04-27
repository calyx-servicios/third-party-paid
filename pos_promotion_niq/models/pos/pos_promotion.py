# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PosPromotion(models.Model):

    _name = 'pos.promotion'

    @api.model
    def _default_pos(self):
        return self.env['pos.config'].search([]).ids


    name = fields.Char('Name', required=True)

    state = fields.Selection(
        string='State',
        selection=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancel')],
        default="draft"
    )
    priority = fields.Integer('Priority', default="15")

    applicable_amount = fields.Float('Require Total Amount')
    discount_total_amount = fields.Float(
        'Total Amount Will Be Disc %',
        help="All total amount of order will be discount % by the value of this field"
    )

    promotion_group = fields.Selection(
        string="Groups",
        selection=[('on_product', 'Base On Product'),
                   ('on_amount', 'Base On Total Amount'),
                   # ('free_select', 'Select Manually')
                   ],
        required=True)

    promotion_type_id = fields.Many2one(
        comodel_name='pos.promotion.type',
        string="Type",
        domain="[('group','=', promotion_group)]",
        required=True
    )
    promotion_code = fields.Char(
        related='promotion_type_id.code',
        string='Code',
        store=True)
    promotion_type = fields.Char(
        related="promotion_type_id.code",
        string="Promotion Code")

    condition_combo_product_ids = fields.One2many(
        comodel_name="pos.promotion.condition.combo",
        inverse_name="promotion_id",
        string="Condition Combo Products"
    )

    promotion_product_ids = fields.One2many(
        comodel_name="pos.promotion.product",
        inverse_name="promotion_id",
        string="Products"
    )
    promotion_template_ids = fields.One2many(
        comodel_name="pos.promotion.template",
        inverse_name="promotion_id",
        string="Product Template"
    )
    promotion_category_ids = fields.One2many(
        comodel_name="pos.promotion.category",
        inverse_name="promotion_id",
        string="Product Category"
    )
    pos_ids = fields.Many2many(
        comodel_name="pos.config",
        default=_default_pos,
        relation="pos_promotion_pos_config_rel",
        string="Pos to apply"
    )
    start_date = fields.Date(
        string=u'Start Date',
        default=fields.Date.context_today
    )
    end_date = fields.Date(
        string=u'End Date',
        default=fields.Date.context_today
    )

    @api.model
    def cron_deactive_expired_promotion(self):
        today = fields.Date.today()
        # fields.Date.from_string(fields.Date.today())
        domain = [
            ('state', '=', 'active'),
            ('end_date', '!=', False),
            ('end_date', '<', today)]
        expired_promotions = self.search(domain)
        expired_promotions.write({'state': 'done'})

    @api.model
    def cron_active_promotion(self):
        today = fields.Date.today()
        print(today, type(today))
        today = fields.Date.to_string(fields.Date.today())
        print(today, type(today))
        domain = [
            ('state', '=', 'draft'),

            ('start_date', '!=', False),
            ('start_date', '<=', today),
            '|',

            '&', ('end_date', '!=', False),
            ('end_date', '>=', today),

            ('end_date', '=', False),
        ]
        promotions = self.search(domain)
        promotions.write({'state': 'active'})

    def button_validate(self):
        self.write({'state': 'active'})

    def button_done(self):
        self.write({'state': 'done'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

    def button_set_draft(self):
        self.write({'state': 'draft'})

    def export_promotion_product(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'inline',
            'url': '/pos_promotion_niq/product/export/?promotion_id=%s' % self.id,
        }

    def web_export_promotion_product(self):
        # prepare data
        promotion_data = []
        columns_headers = [
            'ID', 'Buy X Name', 'X Internal Reference', 'X Barcode',
            'Qty X', 'Product Y', 'Y Internal Reference', 'Y Barcode',
            'Free Qty', 'Fixed Price', 'Discount %', 'Discount Amount'
         ]
        for promotion in self:
            for promotion_product in promotion.promotion_product_ids:
                promotion_data.append([
                    promotion_product.id or '',
                    promotion_product.condition_product_id.name or '',
                    promotion_product.condition_product_id.default_code or '',
                    promotion_product.condition_product_id.barcode or '',
                    promotion_product.condition_qty or '',
                    promotion_product.product_id.name or '',
                    promotion_product.product_id.default_code or '',
                    promotion_product.product_id.barcode or '',
                    promotion_product.free_qty or '',
                    promotion_product.fixed_price or '',
                    promotion_product.disc_percentage or '',
                    promotion_product.disc_amount or '',
                ])
        return columns_headers, promotion_data

    def button_delete_all_promotion_product(self):
        self.ensure_one()
        self.promotion_product_ids.unlink()
