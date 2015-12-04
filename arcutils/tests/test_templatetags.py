from django.http import HttpRequest
from django.template import Context, Template
from django.test import TestCase

from arcutils.templatetags.arc import cdn_url


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
