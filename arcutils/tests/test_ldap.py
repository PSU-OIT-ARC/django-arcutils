from unittest import TestCase

import ldap3

from arcutils.ldap import connect
from arcutils.ldap.profile import (
    parse_email,
    parse_name,
    parse_phone_number,
    parse_psu_extension,
    parse_profile,
)


class TestLDAP(TestCase):

    def test_connect(self):
        cxn = connect(using='default')
        self.assertIsInstance(cxn, ldap3.Connection)


class TestLDAPProfileParsing(TestCase):

    def test_parse_profile(self):
        entry = {
            'sn': ['Johnson'],
            'givenName': ['Matt'],
            'mail': ['mdj2@pdx.edu'],
            'mailLocalAddress': ['matt.johnson@pdx.edu'],
            'mailRoutingAddress': ['mdj2@pdx.edu'],
            'uid': ['mdj2'],
            'ou': [
                'Web Development Team - Office of Information Technology',
                'Blurp - Bloop',
            ],
            'psuPasswordExpireDate': ['20161031121314Z'],
            'telephoneNumber': ['x5-1234']
        }
        result = parse_profile(entry)
        self.assertEqual(result['first_name'], 'Matt')
        self.assertEqual(result['last_name'], 'Johnson')
        self.assertEqual(result['email_address'], 'mdj2@pdx.edu')
        self.assertEqual(result['email_addresses'], ['mdj2@pdx.edu', 'matt.johnson@pdx.edu'])
        self.assertEqual(result['ou'], 'Web Development Team - Office of Information Technology')
        self.assertEqual(result['school_or_office'], 'Office of Information Technology')
        self.assertEqual(result['department'], 'Web Development Team')
        self.assertEqual(result['password_expiration_date'], '20161031T121314Z')
        self.assertEqual(result['phone_number'], '503-725-1234')
        self.assertEqual(result['extension'], '5-1234')

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


class TestPhoneNumberParsing(TestCase):

    def test_ten_digit_number(self):
        num = parse_phone_number(None, '5035551212')
        self.assertEqual(num, '503-555-1212')

    def test_ten_digit_number_with_dashes(self):
        num = parse_phone_number(None, '503-555-1212')
        self.assertEqual(num, '503-555-1212')

    def test_ten_digit_number_with_dots(self):
        num = parse_phone_number(None, '503.555.1212')
        self.assertEqual(num, '503-555-1212')

    def test_ten_digit_number_with_parens_and_dash(self):
        num = parse_phone_number(None, '(503)555-1212')
        self.assertEqual(num, '503-555-1212')

    def test_eleven_digit_number(self):
        num = parse_phone_number(None, '15035551212')
        self.assertEqual(num, '503-555-1212')

    def test_eleven_digit_number_with_dashes(self):
        num = parse_phone_number(None, '1-503-555-1212')
        self.assertEqual(num, '503-555-1212')

    def test_eleven_digit_number_with_dots(self):
        num = parse_phone_number(None, '1.503.555.1212')
        self.assertEqual(num, '503-555-1212')

    def test_four_digit_extension(self):
        num = parse_phone_number(None, '1212')
        self.assertEqual(num, '503-725-1212')

    def test_four_digit_extension_with_x_prefix(self):
        num = parse_phone_number(None, 'x1212')
        self.assertEqual(num, '503-725-1212')

    def test_five_digit_extension(self):
        num = parse_phone_number(None, '51212')
        self.assertEqual(num, '503-725-1212')

    def test_five_digit_extension_with_dash(self):
        num = parse_phone_number(None, '5-1212')
        self.assertEqual(num, '503-725-1212')

    def test_five_digit_extension_with_dot(self):
        num = parse_phone_number(None, '5.1212')
        self.assertEqual(num, '503-725-1212')

    def test_five_digit_extension_with_x_prefix(self):
        num = parse_phone_number(None, 'x51212')
        self.assertEqual(num, '503-725-1212')


class TestPSUExtensionParsing(TestCase):

    def test_psu_number(self):
        ext = parse_psu_extension(None, '503-725-1212')
        self.assertEqual(ext, '5-1212')

    def test_psu_extension(self):
        ext = parse_psu_extension(None, '5-1212')
        self.assertEqual(ext, '5-1212')

    def test_non_psu_number(self):
        ext = parse_psu_extension(None, '503-555-1212')
        self.assertIsNone(ext)

    def test_non_psu_extension(self):
        ext = parse_psu_extension(None, '4-1212')
        self.assertIsNone(ext)
