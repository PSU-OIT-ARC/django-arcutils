from django.test import RequestFactory

from arcutils.test import FunctionalTestCase
from arcutils.response import get_redirect_location


class TestGetRedirectLocation(FunctionalTestCase):

    def setUp(self):
        self.request_factory = RequestFactory()

    def test_set_via_query_params(self):
        request = self.request_factory.get('/', data={'next': '/pants'}, HTTP_REFERER='/xxx')
        location = get_redirect_location(request)
        self.assertEqual(location, '/pants')

    def test_set_in_data(self):
        request = self.request_factory.post('/', data={'next': '/bananas'}, HTTP_REFERER='/xxx')
        location = get_redirect_location(request)
        self.assertEqual(location, '/bananas')

    def test_set_via_query_params_and_in_data(self):
        request = self.request_factory.post(
            '/?next=/pants', data={'next': '/bananas'}, HTTP_REFERER='/xxx')
        location = get_redirect_location(request)
        self.assertEqual(location, '/pants')

    def test_use_referrer(self):
        request = self.request_factory.post('/', HTTP_REFERER='/goodbananas')
        location = get_redirect_location(request)
        self.assertEqual(location, '/goodbananas')

    def test_unsafe_referrer(self):
        request = self.request_factory.post('/', HTTP_REFERER='http://badbananas.org/')
        location = get_redirect_location(request, default='/goodbananas')
        self.assertEqual(location, '/goodbananas')

    def test_default(self):
        request = self.request_factory.post('/')
        location = get_redirect_location(request, default='/goodbananas')
        self.assertEqual(location, '/goodbananas')

    def test_bad_default(self):
        request = self.request_factory.post('/')
        location = get_redirect_location(request, default='http://badbananas.org/')
        self.assertEqual(location, '/')
