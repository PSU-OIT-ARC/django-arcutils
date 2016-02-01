from django.db import connection
from django.test import TestCase

from arcutils.db import dictfetchall, will_be_deleted_with, ChoiceEnum
from arcutils.test.user import UserMixin


class TestDictFetchAll(UserMixin, TestCase):

    def test(self):
        user1 = self.create_user(username='user1')
        user2 = self.create_user(username='user2')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM auth_user ORDER BY username')
        results = dictfetchall(cursor)
        self.assertEqual(len(results), 2)
        self.assertIn('username', results[0])
        self.assertEqual(results[0]['username'], user1.username)
        self.assertIn('username', results[1])
        self.assertEqual(results[1]['username'], user2.username)


class TestWillBeDeletedWith(UserMixin, TestCase):

    def test_will_be_deleted_with(self):
        user = self.create_user(username='user', groups=('group-a', 'group-b'))
        self.create_user(username='xxx', groups=('group-a'))
        self.create_user(username='yyy', groups=('group-a'))

        results = will_be_deleted_with(user)
        record_type, records = next(results)

        # The user shouldn't be in the list of additional objects to be
        # deleted.
        self.assertNotIn(user, records)

        # When the user is deleted, the associated records in
        # auth_user_groups should be deleted too.
        self.assertEqual(record_type._meta.db_table, 'auth_user_groups')
        self.assertEqual(len(records), 2)
        for r in records:
            self.assertEqual(r.user, user)


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
