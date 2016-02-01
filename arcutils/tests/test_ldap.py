from django.test import TestCase

import ldap3

from arcutils.ldap import parse_profile, parse_email, parse_name, connect


class TestLdap(TestCase):

    def test_connect(self):
        cxn = connect(using='default')
        self.assertIsInstance(cxn, ldap3.Connection)

    def test_parse_profile(self):
        entry = {
            'sn': ['Johnson'],
            'givenName': ['Matt'],
            'mail': ['mdj2@pdx.edu'],
            'mailLocalAddress': ['matt.johnson@pdx.edu'],
            'mailRoutingAddress': ['mdj2@pdx.edu'],
            'uid': ['mdj2'],
            'ou': [
                'Academic & Research Computing - Office of Information Technology',
                'Blurp - Bloop',
            ],
            'psuPasswordExpireDate': ['20161031121314Z'],
        }
        result = parse_profile(entry)
        self.assertEqual(result['first_name'], 'Matt')
        self.assertEqual(result['last_name'], 'Johnson')
        self.assertEqual(result['email_address'], 'mdj2@pdx.edu')
        self.assertEqual(result['email_addresses'], ['mdj2@pdx.edu', 'matt.johnson@pdx.edu'])
        self.assertEqual(result['ou'], 'Academic & Research Computing - Office of Information Technology')
        self.assertEqual(result['school_or_office'], 'Office of Information Technology')
        self.assertEqual(result['department'], 'Academic & Research Computing')
        self.assertEqual(result['password_expiration_date'], '20161031T121314Z')

    def test_parse_email(self):
        self.assertEqual('foo@bar.com', parse_email({'mail': ['foo@bar.com']}))

    def test_parse_email_from_uid(self):
        self.assertEqual('foo@pdx.edu', parse_email({'uid': ['foo']}))

    def test_parse_name(self):
        self.assertEqual(('John', 'Doe'), parse_name({
            'sn': ['Doe'],
            'givenName': ['John']
        }))
        self.assertEqual(('John', 'Doe'), parse_name({
            'preferredcn': ['John Doe'],
            'givenName': ['John']
        }))
        self.assertEqual(('John', 'Doe'), parse_name({
            'cn': ['John Rake Doe'],
            'givenName': ['John']
        }))
        self.assertEqual(('John', ''), parse_name({
            'givenName': ['John']
        }))
        self.assertEqual(('John', 'Doe'), parse_name({
            'sn': ['Doe'],
            'preferredcn': ['John Rake Doe']
        }))
        self.assertEqual(('John', 'Doe'), parse_name({
            'sn': ['Doe'],
            'cn': ['John Rake Doe']
        }))
        self.assertEqual(('', 'Doe'), parse_name({
            'sn': ['Doe'],
        }))
