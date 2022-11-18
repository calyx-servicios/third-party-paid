# -*- coding: utf-8 -*-

import base64
from odoo import http, api
from odoo import fields, osv
from odoo.http import Controller, Response, request, route
import pdb
import logging
_logger = logging.getLogger(__name__)

from odoo.addons.web.controllers.main import content_disposition
from odoo.addons.odoo_connector_api.controllers.main import OcapiAuthorize
from odoo.addons.odoo_connector_api.controllers.main import OcapiCatalog

class ProductecaAuthorize(OcapiAuthorize):

    @http.route()
    def authorize(self, connector, **post):
        _logger.info("connector:"+str(connector))
        if connector and connector=="producteca":
            return self.producteca_authorize(**post)
        else:
            return super(OcapiAuthorize, self).authorize( connector, **post )

    def producteca_authorize(self, **post):
        #POST api user id and token, create id based on URL if need to create one
        #check all connectors
        #_logger.info("post:"+str(post))
        client_id = post.get("client_id") or post.get("app_id")
        secret_key = post.get("secret_key") or post.get("app_key")
        connection_account = []
        if client_id and secret_key:
            _logger.info("Authentication request for producteca")
            connection_account = request.env['producteca.account'].sudo().search([('client_id','=',client_id),('secret_key','=',secret_key)])
        access_tokens = []
        if not connection_account:
            _logger.error("No response for: client_id:"+str(client_id)+" secret_key:" + str(secret_key) )
        for a in connection_account:
            _logger.info("Trying")
            access_token = a.authorize_token( client_id, secret_key )
            access_tokens.append({ 'client_id': client_id, 'access_token': access_token  })
        _logger.info(access_tokens)
        return access_tokens


class ProductecaCatalog(OcapiCatalog):

    def get_producteca_connection(self, **post):

        connector = "producteca"

        access_token = post.get("access_token")

        if not access_token:
            return False

        connection_account = request.env['producteca.account'].sudo().search([('access_token','=',access_token)])

        _logger.info(connection_account)

        if not connection_account or not len(connection_account)==1:
            return False

        if not (connector == connection_account.type):
            return False

        return connection_account

    def get_connection_account(self, connector,**post):
        if connector and connector=="producteca":
            return self.get_producteca_connection(**post)
        else:
            return super(OcapiCatalog, self).get_connection(connector,**post)
