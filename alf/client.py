# -*- coding: utf-8 -*-

import requests

from alf.managers import SimpleTokenManager


class BearerTokenAuth(requests.auth.AuthBase):

    def __init__(self, access_token):
        self._access_token = access_token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer {}'.format(self._access_token)


class Client(requests.Session):

    def __init__(self, *args, **kwargs):
        self._token_endpoint = kwargs.pop('token_endpoint')
        self._client_id = kwargs.pop('client_id')
        self._client_secret = kwargs.pop('client_secret')

        self._token_manager = SimpleTokenManager(
            token_endpoint=self._token_endpoint,
            client_id=self._client_id,
            client_secret=self._client_secret)

        super(Client, self).__init__(*args, **kwargs)

    def _request(self, *args, **kwargs):
        access_token = self._token_manager.get_token()
        kwargs['auth'] = BearerTokenAuth(access_token)
        return super(Client, self).request(*args, **kwargs)

    def _retry_request(self, *args, **kwargs):
        self._token_manager.request_token()
        return self._request(*args, **kwargs)

    def request(self, *args, **kwargs):
        if not self._token_manager.has_token():
            self._token_manager.request_token()

        response = self._request(*args, **kwargs)
        if response.status_code != 401:
            return response

        return self._retry_request(*args, **kwargs)