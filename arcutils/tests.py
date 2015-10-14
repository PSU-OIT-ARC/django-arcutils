from doctest import DocTestSuite
from mock import Mock
from model_mommy.mommy import make
from django.test import TestCase
from django.http import HttpRequest
from django.conf import settings
from django.forms.util import ErrorDict
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.template import Context, Template

from . import colorize
from .db import dictfetchall, will_be_deleted_with, ChoiceEnum
from .forms import FormSetMixin, BaseFormSet, BaseModelFormSet
from .ldap import parse_profile, parse_email, parse_name, connect
from .templatetags import arc as arc_tags


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(colorize))
    return tests


class TestDictFetchAll(TestCase):
    def setUp(self):
        make(get_user_model())
        make(get_user_model())

    def test(self):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM auth_user")
        results = dictfetchall(cursor)
        results[0]['last_name']
        results[1]['last_name']


class TestWillBeDeletedWith(TestCase):
    def setUp(self):
        self.group_a = make(Group)
        self.group_b = make(Group)
        self.user = make(get_user_model())

        self.group_a.user_set.add(self.user)
        self.group_b.user_set.add(self.user)

        self.group_a.user_set.add(make(get_user_model()))
        self.group_a.user_set.add(make(get_user_model()))

    def test(self):
        results = list(will_be_deleted_with(self.user))
        # make sure the object we are deleting isn't included
        for cls, result_set in results:
            self.assertNotIn(self.user, result_set)

        self.assertEqual(len(results[0][1]), 2)


class TestChoiceEnum(TestCase):
    def setUp(self):
        class Foo(ChoiceEnum):
            alpha = 1
            beta = 2

            _choices = (
                (alpha, "Alpha"),
                (beta, "Beta"),
            )

        self.Foo = Foo

    def test(self):
        self.assertEqual(list(self.Foo), list(self.Foo._choices))


class TestLdap(TestCase):
    def test_connect(self):
        conn = connect(using="default")
        self.assertTrue(conn)
        self.assertIn("_server", settings.LDAP['default'])

    def test_parse_profile(self):
        entry = {
            "sn": ["Johnson"],
            "givenName": ['Matt'],
            "mail": ["mdj2@pdx.edu"],
            "uid": ["mdj2"],
            "ou": [
                'Academic & Research Computing - Office of Information Technology',
                'Blurp - Bloop',
            ],
        }
        result = parse_profile(entry)
        self.assertEqual(result['first_name'], "Matt")
        self.assertEqual(result['last_name'], "Johnson")
        self.assertEqual(result['email'], "mdj2@pdx.edu")
        self.assertEqual(result['ou'], 'Academic & Research Computing - Office of Information Technology')
        self.assertEqual(result['school_or_office'], 'Office of Information Technology')
        self.assertEqual(result['department'], 'Academic & Research Computing')

    def test_parse_email(self):
        self.assertEqual("foo@bar.com", parse_email({"mail": ["foo@bar.com"]}))
        self.assertEqual("foo@pdx.edu", parse_email({"uid": ["foo"]}))

    def test_parse_name(self):
        # test the last name login
        self.assertEqual(("John", "Doe"), parse_name({
            "sn": ["Doe"],
            "givenName": ["John"]
        }))
        self.assertEqual(("John", "Doe"), parse_name({
            "preferredcn": ["John Doe"],
            "givenName": ["John"]
        }))
        self.assertEqual(("John", "Doe"), parse_name({
            "cn": ["John Rake Doe"],
            "givenName": ["John"]
        }))
        self.assertEqual(("John", ""), parse_name({
            "givenName": ["John"]
        }))

        # test the first_name login
        self.assertEqual(("John", "Doe"), parse_name({
            "sn": ["Doe"],
            "preferredcn": ["John Rake Doe"]
        }))
        self.assertEqual(("John", "Doe"), parse_name({
            "sn": ["Doe"],
            "cn": ["John Rake Doe"]
        }))
        self.assertEqual(("", "Doe"), parse_name({
            "sn": ["Doe"],
        }))


class TestFormSetMixin(TestCase):
    def test_iter_with_empty_form_first(self):
        """Ensure it chains the empty_form with the rest of the iterable"""
        fs = FormSetMixin()
        fs.empty_form = 1
        FormSetMixin.__iter__ = lambda cls: iter([2, 3, 4])
        self.assertEqual([1, 2, 3, 4], list(fs.iter_with_empty_form_first()))

    def test_clean(self):
        fs = FormSetMixin()
        form_a = Mock()
        form_a.cleaned_data = {"DELETE": True}
        form_a._errors = ErrorDict({"name": "That's not a valid name"})

        form_b = Mock()
        form_b.cleaned_data = {"name": "John"}
        form_b._errors = ErrorDict()

        form_c = Mock()
        form_c.cleaned_data = {}
        form_c._errors = ErrorDict({"name": "That's not a valid name"})

        fs.forms = [form_a, form_b, form_c]
        fs.clean()
        self.assertEqual(form_a._errors, ErrorDict())

    def test_inheritance(self):
        self.assertTrue(issubclass(BaseFormSet, FormSetMixin))
        self.assertTrue(issubclass(BaseModelFormSet, FormSetMixin))


class TestCDNURLTag(TestCase):

    def test_cdn_url_has_no_scheme_by_default(self):
        self.assertEqual(arc_tags.cdn_url('/x/y/z'), '//cdn.research.pdx.edu/x/y/z')

    def test_leading_slash_is_irrelevant(self):
        self.assertEqual(arc_tags.cdn_url('/x/y/z'), '//cdn.research.pdx.edu/x/y/z')
        self.assertEqual(arc_tags.cdn_url('x/y/z'), '//cdn.research.pdx.edu/x/y/z')

    def test_with_explicit_scheme(self):
        self.assertEqual(
            arc_tags.cdn_url('/x/y/z', scheme='http'),
            'http://cdn.research.pdx.edu/x/y/z')

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
