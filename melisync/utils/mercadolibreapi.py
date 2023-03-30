from .utils import Requests
import logging
logger = logging.getLogger(__name__)

class MercadoLibreClient(object):
    # Default API URL
    _API_URL = 'https://api.mercadolibre.com'
    # Default authorization url
    _AUTHORIZATION_URL = 'https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&state={state}'

    def __init__(self, client_id, client_secret, redirect_uri):
        """
            Class Start
                Args:
                    client_id: Application ID
                    client_secret: Application client secret
                    redirect_uri: Application URL
                    api_url: Mercadolibre API URL

            Documentation: https://developers.mercadolibre.com.ar/es_ar/api-docs-es
        """
        # Args
        self.params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
        }
        # Default data
        self.default_headers = {
            'accept': 'application/json',
        }
        # Set user ID flag
        self.user_id = None
        # Set requests object
        def _error_parser_fn(res):
            """
                Throw error if res has errors.
            """
            if isinstance(res, dict):
                #logger.info('='*100)
                #logger.info('res = {}'.format(res))
                # If res has error
                if res.get('error'):
                    # Get causes
                    causes = sorted(res.get('cause', []), key=lambda d: d['type'])
                    # Array with causes
                    errors = ['- [{}] {}: {}'.format(x.get('type'), x.get('code'), x.get('message')) for x in causes]
                    # Exception lines
                    raise Exception('\n\n[{}] {}:\n\n{}'.format(res.get('error'), res.get('message'), '\n'.join(errors)))
        self.requests_obj = Requests(self._API_URL, self.default_headers, _error_parser_fn)

    def get_authorization_url(self, state):
        """
            Get authorization URL to get Authorization Code.
        """
        params = { **self.params, 'state': state }
        return self._AUTHORIZATION_URL.format(**params)

    def get_refresh_token(self, authorization_code):
        """
            To exchange authorization code by Access Token.
            Params:
                - authorization_code: authorization code obtained by url redirection from MercadoLibre.
        """
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.params.get('client_id'),
            'client_secret': self.params.get('client_secret'),
            'code': authorization_code,
            'redirect_uri': self.params.get('redirect_uri'),
        }
        response = self.requests_obj._post('/oauth/token', data = data)
        # Save token
        token_data = {
            'token_type': response.get('token_type').capitalize(),
            'access_token': response.get('access_token'),
        }
        self.default_headers['Authorization'] = '{token_type} {access_token}'.format(**token_data)
        # Save the user ID
        self.user_id = response.get('user_id')
        return response
    
    def get_access_token(self, refresh_token):
        """
            To refresh Access Token if due.
            Params:
                - refresh_token: refresh token Code.
        """
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.params.get('client_id'),
            'client_secret': self.params.get('client_secret'),
            'refresh_token': refresh_token,
        }
        response = self.requests_obj._post('/oauth/token', data = data)
        # Save token
        token_data = {
            'token_type': response.get('token_type').capitalize(),
            'access_token': response.get('access_token'),
        }
        self.default_headers['Authorization'] = '{token_type} {access_token}'.format(**token_data)
        # Save the user ID
        self.user_id = response.get('user_id')
        return response

    def create_test_user(self, site_id):
        """
            Create test user.
            Parameters:
                - site_id: site ID to register new test user.
        """
        return self.requests_obj._post('/users/test_user', json = { 'site_id': site_id })

    def me(self):
        """
            User account information.
        """
        return self.requests_obj._get('/users/me')

    def get_user(self, user_id):
        """
            User account information.
        """
        return self.requests_obj._get(f'/users/{user_id}')

    def get_sites(self):
        """
            Retrieves information about the sites where MercadoLibre runs.
        """
        return self.requests_obj._get('/sites')

    def get_listing_types(self, site_id):
        """
            Returns information about listing types.
            Parameters:
                - site_id: site ID.
        """
        return self.requests_obj._get(f'/sites/{site_id}/listing_types')

    def get_category_attributes(self, category_id):
        """
            Return category attributes.
            Parameters:
                - category_id: id of category.
        """
        return self.requests_obj._get(f'/categories/{category_id}/attributes')

    def get_currencies(self):
        """	
            Returns information about all available currencies in MercadoLibre.
        """
        return self.requests_obj._get('/currencies')

    def category_predictor(self, site_id, product_name, limit = 8):
        """
            Return a list of dict, each dict contains the key category_id.
            Parameters:
                - product_name: name of products
                - limit: the limit value default return is 1, but you can configure between 1 and 8
        """
        # Define query parameters.
        params = {
            'q': product_name,
            'limit': limit,
        }
        return self.requests_obj._get(f'/sites/{site_id}/domain_discovery/search', params=params)

    def item_create(self, item_data):
        """
            Create a product in MercadoLibre.
            Parameters:
                - item_data: obj with item data.
        """
        return self.requests_obj._post('/items', json = item_data)

    def item_update(self, item_id, item_data):
        """
            Update a product in MercadoLibre.
            Parameters:
                - item_id: published item ID.
                - item_data: new item data.
        """
        return self.requests_obj._put(f'/items/{item_id}', json = item_data)

    def item_variation_create(self, item_id, variant_data):
        """
            Add product variant in MercadoLibre.
            Parameters:
                - item_id: published item ID.
                - variant_data: variation data.
        """
        return self.requests_obj._post(f'/items/{item_id}/variations', json = variant_data)

    def item_variation_delete(self, item_id, variation_id):
        """
            Add product variant in MercadoLibre.
            Parameters:
                - item_id: published item ID.
                - variation_id: variation id.
        """
        return self.requests_obj._delete(f'/items/{item_id}/variations/{variation_id}')

    def item_post_description(self, item_id, data):
        """
            Post a product description in MercadoLibre.
            Parameters:
                - item_id: published item ID.
                - data: { **description_data }
        """
        return self.requests_obj._put(f'/items/{item_id}/description', json = data)

    def item_update_description(self, item_id, data):
        """
            Update a product description in MercadoLibre.
            Parameters:
                - item_id: published item ID.
                - data: { **description_data }
        """
        return self.requests_obj._put(f'/items/{item_id}/description', json = data)

    def item_get(self, item_id):
        """
            Update a product in MercadoLibre.
            Parameters:
                - item_id: published item ID.
        """
        return self.requests_obj._get(f'/items/{item_id}')
    
    def item_picture_upload(self, files):
        """
            Upload item image.
            Parameters:
                - files: object with files.
        """
        return self.requests_obj._post('/pictures/items/upload', files=files)
    
    def item_picture_add(self, item_id, picture_id):
        """
            Add item image.
            Parameters:
                - item_id: item id
                - picture_id: new picture_id
        """
        return self.requests_obj._post(f'/items/{item_id}/pictures', json = { 'id': picture_id })

    def get_orders(self, params={}):
        """	
            Get orders.
            Parameters:
                - params: custom filter.
            Info: https://developers.mercadolibre.com.ar/es_ar/gestiona-ventas#Buscar-ordenes
        """
        return self.requests_obj._get('/orders/search', params=params)

    def get_sale_billing_info(self, order_id):
        """	
            Get order billing info.
            Parameters:
                - order_id: order ID
            Info: https://developers.mercadolibre.com.ar/es_ar/gestiona-ventas#Buscar-ordenes
        """
        return self.requests_obj._get(f'/orders/{order_id}/billing_info')

    def get_site_categories(self, site_id):
        """
            Return site categories.
            Parameters:
                - site_id: site ID.
        """
        return self.requests_obj._get(f'/sites/{site_id}/categories')

    def get_category_data(self, categ_id):
        """
            Return category data.
            Parameters:
                - categ_id: category ID.
        """
        return self.requests_obj._get(f'/categories/{categ_id}')

    def get_all_categories(self, site_id, withAttributes=False):
        """
            Get all categories
            Parameters:
                - site_id: site ID.
                - withAttributes: get all categories attributes.
        """
        params = {}
        if withAttributes:
            params['withAttributes'] = 'true'
        return self.requests_obj._get(f'/sites/{site_id}/categories/all', params=params)

    def get_shipping_methods(self, site_id):
        """
            Return site shipping methods.
            Parameters:
                - site_id: site ID.
        """
        return self.requests_obj._get(f'/sites/{site_id}/shipping_methods')
