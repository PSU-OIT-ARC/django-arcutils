from django.http import HttpRequest
from django.template import Context, Template
from django.test import TestCase

from arcutils.templatetags.arc import cdn_url, google_analytics


class TestCDNURLTag(TestCase):

    def test_cdn_url_has_no_scheme_by_default(self):
        self.assertEqual(cdn_url('/x/y/z'), '//cdn.research.pdx.edu/x/y/z')

    def test_leading_slash_is_irrelevant(self):
        self.assertEqual(cdn_url('/x/y/z'), '//cdn.research.pdx.edu/x/y/z')
        self.assertEqual(cdn_url('x/y/z'), '//cdn.research.pdx.edu/x/y/z')

    def test_with_explicit_scheme(self):
        self.assertEqual(cdn_url('/x/y/z', scheme='http'), 'http://cdn.research.pdx.edu/x/y/z')

    def test_integration(self):
        template = Template('{% load arc %}{% cdn_url "/x/y/z" %}')
        request = HttpRequest()
        output = template.render(Context({'request': request}))
        self.assertEqual(output, '//cdn.research.pdx.edu/x/y/z')

    def test_integration_with_scheme(self):
        template = Template('{% load arc %}{% cdn_url "/x/y/z" scheme="http" %}')
        request = HttpRequest()
        output = template.render(Context({'request': request}))
        self.assertEqual(output, 'http://cdn.research.pdx.edu/x/y/z')


class TestGoogleAnalyticsTag(TestCase):

    tracking_id = 'UA-XXXXX-Y'

    def test_ga_script_tag_is_returned_with_defaults(self):
        output = google_analytics(self.tracking_id).strip()
        self.assertTrue(output.startswith('<script>'))
        self.assertTrue(output.endswith('</script>'))
        self.assertIn(self.tracking_id, output)
        output_lower = output.lower()
        self.assertRegex(output_lower, r'%s.+//\s+tracking id' % self.tracking_id.lower())
        self.assertRegex(output_lower, r'auto.+//\s+cookie domain')
        self.assertRegex(output_lower, r'undefined.+//\s+tracker name')
        self.assertRegex(output_lower, r'undefined.+//\s+fields')

    def test_ga_script_tag_is_returned_with_options(self):
        output = google_analytics(
            self.tracking_id,
            cookie_domain='example.com',
            tracker_name='example',
            fields={'example': 'example'},
        ).strip()
        self.assertTrue(output.startswith('<script>'))
        self.assertTrue(output.endswith('</script>'))
        self.assertIn(self.tracking_id, output)
        output_lower = output.lower()
        self.assertRegex(output_lower, r'example\.com.+//\s+cookie domain')
        self.assertRegex(output_lower, r'example.+//\s+tracker name')
        self.assertRegex(output_lower, r'\{"example": "example"\}.+//\s+fields')

    def test_html_placeholder_is_returned_in_debug_mode(self):
        with self.settings(DEBUG=True):
            output = google_analytics(self.tracking_id).strip()
            self.assertTrue(output.startswith('<!--'))
            self.assertTrue(output.endswith('-->'))
            self.assertNotIn(self.tracking_id, output)

    def test_html_placeholder_is_returned_when_no_tracking_id_specified(self):
        with self.settings(DEBUG=False):
            output = google_analytics()
            self.assertTrue(output.startswith('<!--'))
            self.assertTrue(output.endswith('-->'))
            self.assertNotIn(self.tracking_id, output)


class TestRedirectLocation(TestCase):

    def _make_request(self, **meta):
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'arcutils.test'
        request.META['SERVER_PORT'] = 80
        request.META.update(meta)
        return request

    def test_no_referrer_and_no_default(self):
        template = Template('{% load arc %}{% redirect_location %}')
        request = self._make_request()
        output = template.render(Context({'request': request}))
        self.assertEqual(output, '/')

    def test_referrer_and_no_default(self):
        template = Template('{% load arc %}{% redirect_location %}')
        request = self._make_request(HTTP_REFERER='/previous')
        output = template.render(Context({'request': request}))
        self.assertEqual(output, '/previous')

    def test_no_referrer_and_default(self):
        template = Template('{% load arc %}{% redirect_location default_location="/previous" %}')
        request = self._make_request()
        output = template.render(Context({'request': request}))
        self.assertEqual(output, '/previous')

    def test_no_referrer_and_default_route_name(self):
        template = Template('{% load arc %}{% redirect_location default_location="test" %}')
        request = self._make_request()
        output = template.render(Context({'request': request}))
        self.assertEqual(output, '/test')
