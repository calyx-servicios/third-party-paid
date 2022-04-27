# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"
    _description = "Point of Sale Orders Statistics"

    total_promo_disc_percentage = fields.Float(string='Disc %', readonly=True)
    total_promo_disc_amount = fields.Float(string='Disc Amount', readonly=True)
    total_promo_fixed_price = fields.Float(string='Fixed Price', readonly=True)
    total_promo_get_free = fields.Float(string='Free Amount', readonly=True)

    def _select(self):
        return """
            SELECT
                MIN(l.id) AS id,
                COUNT(*) AS nbr_lines,
                s.date_order AS date,
                SUM(l.qty) AS product_qty,
                SUM(l.qty * l.price_unit) AS price_sub_total,


                SUM(
                    CASE
                        WHEN (l.discount > 0 OR l.discount > 0)
                            THEN (l.qty * l.price_unit * (100 - l.discount) / 100 * (100 - COALESCE(l.discount, 0))/100)
                        WHEN (l.promo_disc_amount > 0 OR l.promo_get_free)
                            THEN (l.qty * (l.price_unit - l.promo_disc_amount))
                        WHEN (l.promo_fixed_price > 0)
                            THEN (l.qty * promo_fixed_price)
                        ELSE
                            (l.qty * l.price_unit)
                    END) AS price_total,

                SUM(
                    (l.qty * l.price_unit) -
                        (CASE
                            WHEN (l.discount > 0 OR l.discount > 0)
                                THEN (l.qty * l.price_unit * (100 - l.discount) / 100 * (100 - COALESCE(l.discount, 0))/100)
                            ELSE
                                l.qty * l.price_unit
                        END)
                    ) AS total_promo_disc_percentage,
                SUM(
                    CASE
                        WHEN (l.promo_disc_amount > 0 AND l.promo_get_free IS FALSE)
                        THEN l.qty * l.promo_disc_amount
                        ELSE 0
                    END) AS total_promo_disc_amount,

                SUM(
                    CASE
                        WHEN l.promo_fixed_price > 0 THEN l.qty * (l.price_unit - l.promo_fixed_price)
                        ELSE 0
                    END
                    ) AS total_promo_fixed_price,

                SUM(
                    CASE
                        WHEN l.promo_get_free IS TRUE
                        THEN (l.qty * l.price_unit)
                        ELSE 0
                    END) AS total_promo_get_free,

                SUM(
                        (l.qty * l.price_unit) -
                        (CASE
                            WHEN (l.discount > 0 OR l.discount > 0)
                                THEN (l.qty * l.price_unit * (100 - l.discount) / 100 * (100 - COALESCE(l.discount, 0))/100)
                            WHEN (l.promo_disc_amount > 0 OR l.promo_get_free)
                                THEN (l.qty * (l.price_unit - l.promo_disc_amount))
                            WHEN (l.promo_fixed_price > 0)
                                THEN (l.qty * promo_fixed_price)
                            ELSE
                                l.qty * l.price_unit
                        END)
                    ) AS total_discount,
                (SUM(l.qty*l.price_unit)/SUM(l.qty * u.factor))::decimal AS average_price,
                SUM(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') AS INT)) AS delay_validation,
                s.id as order_id,
                s.partner_id AS partner_id,
                s.state AS state,
                s.user_id AS user_id,
                s.location_id AS location_id,
                s.company_id AS company_id,
                s.sale_journal AS journal_id,
                l.product_id AS product_id,
                pt.categ_id AS product_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                pt.pos_categ_id,
                spt.default_location_src_id,
                s.pricelist_id,
                s.session_id
        """

    def _from(self):
        return """
            FROM pos_order_line AS l
                LEFT JOIN pos_order s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                LEFT JOIN pos_session ps ON (s.session_id=ps.id)
                LEFT JOIN pos_config pc ON (ps.config_id=pc.id)
                LEFT JOIN stock_picking_type spt ON (spt.id=pc.picking_type_id)
        """

    def _group_by(self):
        return """
            GROUP BY
                s.id, s.date_order, s.partner_id,s.state, pt.categ_id,
                s.user_id, s.location_id, s.company_id, s.sale_journal,
                s.pricelist_id, s.create_date, s.session_id,
                l.product_id,
                pt.categ_id, pt.pos_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                spt.default_location_src_id
        """
