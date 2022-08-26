import requests
import gzip

class Requests(object):
    def __init__(self, base_url, default_headers):
        """
            Init requests class
            Parameters:
                - Base URL: url
        """
        self.base_url = base_url
        self.default_headers = default_headers

    def _get(self, endpoint, **kwargs):
        # Generate a GET request
        return self._request('GET', endpoint, **kwargs)

    def _post(self, endpoint,  **kwargs):
        # generate a POST request
        return self._request('POST', endpoint, **kwargs)

    def _put(self, endpoint, **kwargs):
        # Generate a PUT request
        return self._request('PUT', endpoint, **kwargs)

    def _request(self, method, endpoint, custom_headers={}, **kwargs):
        # Generate RESPONSE all request
        headers = {
            **self.default_headers,
            **custom_headers,
        }
        try:
            request = requests.request(method, self.base_url + endpoint, headers = headers, **kwargs)
            return self._parse(request)
        except Exception as e:
            raise Exception(e)

    def _parse(self, request):
        # Parse request data
        return request.json() if 'application/json' in request.headers['Content-Type'] else request.text