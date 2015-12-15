from django.db import connection
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from model_mommy.mommy import make

from arcutils.db import dictfetchall, will_be_deleted_with, ChoiceEnum


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

    class Foo(ChoiceEnum):

        alpha = 1
        beta = 2

    class Status(ChoiceEnum):

        new = 'new'
        open = 'open'

    def test_choices(self):
        self.assertEqual(self.Foo.as_choices(), [(1, 'Alpha'), (2, 'Beta')])

    def test_choices_with_text_values(self):
        self.assertEqual(self.Status.as_choices(), [('new', 'New'), ('open', 'Open')])
