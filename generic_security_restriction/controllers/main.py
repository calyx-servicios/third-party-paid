import logging

from werkzeug import urls

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.main import Home, ensure_db

_logger = logging.getLogger(__name__)

NO_PHRASES = ('', '0', 'false', 'n', 'no', 'f', 'off')
# Debug enabled if in query parameters debug equal to:
# '1',  'assets', 'assets,tests' or any other phrases
# Example: debug=true, debug=True, debug=1, debug=abcdef etc.


class GenericSecurityRestrictionHome(Home):

    @http.route()
    def web_client(self, s_action=None, **kw):
        ensure_db()
        debug_mode = request.session.debug or kw.get('debug', '')

        # Phrases are discovered experimentally, because the original source
        # or method that converts the phrase from the query parameters
        # has not yet been found.
        if debug_mode.lower() in NO_PHRASES:
            return super(GenericSecurityRestrictionHome, self).web_client(
                s_action=s_action, **kw)

        session_user = http.request.env['res.users'].browse([
            http.request.session.uid])

        if not session_user._gsr_is_debug_mode_allowed():
            # Clear debug mode from arguments and session
            # TODO: Check disabling debug mode
            request.session.debug = ''

            url = urls.url_parse(http.request.httprequest.url)
            url_params = url.decode_query()
            url_params = url_params.to_dict()
            url_params.pop('debug', None)
            url_local = url.replace(
                scheme='', netloc='',
                query=urls.url_encode(url_params),
            ).to_url()

            return http.local_redirect(path=url_local)

        return super(GenericSecurityRestrictionHome, self).web_client(
            s_action=s_action, **kw)
