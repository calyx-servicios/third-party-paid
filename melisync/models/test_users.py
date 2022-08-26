# -*- coding: utf-8 -*-
from odoo import models, fields, _
import logging
logger = logging.getLogger(__name__)

class TestUsers(models.Model):
    _name = 'melisync.test.users'
    _description = 'MercadoLibre Test Users Model'
    _rec_name = "email"

    site_id = fields.Many2one(required=True, comodel_name='melisync.site.ids', string=_('Site ID'))
    user_id = fields.Integer(unique=True, required=True, string=_('User ID'))
    email = fields.Char(unique=True, required=True, string=_('Email'))
    nickname = fields.Char(unique=True, required=True, string=_('Nickname'))
    password = fields.Char(required=True, string=_('Password'))
    site_status = fields.Char(required=True, string=_('Site status'))
