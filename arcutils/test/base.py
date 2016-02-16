import json

import django.test

from .user import UserMixin


class Client(django.test.Client):

    def patch_json(self, path, data=None, **kwargs):
        return self.patch(path, **self._json_kwargs(data, kwargs))

    def post_json(self, path, data=None, **kwargs):
        return self.post(path, **self._json_kwargs(data, kwargs))

    def put_json(self, path, data=None, **kwargs):
        return self.put(path, **self._json_kwargs(data, kwargs))

    def _json_kwargs(self, data, kwargs):
        if data is not None:
            data = json.dumps(data)
        kwargs['data'] = data
        kwargs['content_type'] = 'application/json'
        return kwargs


class FunctionalTestCase(django.test.TestCase, UserMixin):

    """Base class for view tests.

    It adds the following to Django's `TestCase`:

        - Convenient user creation & login
        - Convenient POSTs, PUTs, and PATCHes with a JSON body

    """

    client_class = Client
