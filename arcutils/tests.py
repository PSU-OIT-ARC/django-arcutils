from __future__ import absolute_import
from model_mommy.mommy import make
from django.test import TestCase
from django.http import HttpRequest, QueryDict
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.template import Context, Template
from . import PasswordResetForm, dictfetchall, will_be_deleted_with, ChoiceEnum
from .ldap import parse_profile

class TestPasswordResetForm(TestCase):
    def setUp(self):
        make(get_user_model(), email="lame@example.com", is_active=1)

    def test_exeception_raised_when_email_does_not_exist(self):
        form = PasswordResetForm({"email": "foo@bar.com"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_exeception_not_raised_when_email_does_not_exist(self):
        form = PasswordResetForm({"email": "lame@example.com"})
        self.assertTrue(form.is_valid())


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


class TestModelName(TestCase):
    def test(self):
        t = Template("{{ model|model_name }}")
        output = t.render(Context({"model": get_user_model()}))
        self.assertEqual("User", output)


class TestFullUrl(TestCase):
    def test(self):
        t = Template("{% full_url 'login' %}")
        # try rendering with the HTTP_HOST in the request object
        output = t.render(Context({"request": {"HTTP_HOST": "example.com"}}))
        self.assertEqual("example.com/login", output)

        # try rendering with the HOST_NAME in the settings file
        with self.settings(HOST_NAME="example.com"):
            output = t.render(Context())
            self.assertEqual("example.com/login", output)

        # try rendering with the HOSTNAME in the settings file
        with self.settings(HOSTNAME="example.com"):
            output = t.render(Context())
            self.assertEqual("example.com/login", output)


class TestAddGet(TestCase):
    def test(self):
        t = Template("{% add_get page=1 next=variable %}")
        # try rendering with the HTTP_HOST in the request object
        request = HttpRequest()
        request.GET = QueryDict("foo=1&foo=2&bar=lame")

        output = t.render(Context({
            "request": request,
            "variable": "lame",
        }))
        self.assertEqual(output, "?foo=1&foo=2&bar=lame&page=1&next=lame")


class TestLdap(TestCase):
    def test_parse_profile(self):
        entry = {
            "sn": ["Johnson"],
            "givenName": ['Matt'],
            "mail": ["mdj2@pdx.edu"],
        }
        result = parse_profile(entry)
        self.assertEqual(result['first_name'], "Matt")
        self.assertEqual(result['last_name'], "Johnson")
        self.assertEqual(result['email'], "mdj2@pdx.edu")
