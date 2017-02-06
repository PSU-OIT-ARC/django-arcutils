from django.test import override_settings, SimpleTestCase

from arcutils.settings import NO_DEFAULT, PrefixedSettings, get_setting


@override_settings(ARC={
    'a': 'a',
    'b': [0, 1],
    'c': [{'c': 'c'}],
    'd': 'd',
})
class TestGetSettings(SimpleTestCase):

    def get_setting(self, key, default=NO_DEFAULT):
        return get_setting(key, default=default)

    def test_can_traverse_into_dict(self):
        self.assertEqual(self.get_setting('ARC.a'), 'a')

    def test_can_traverse_into_dict_then_list(self):
        self.assertEqual(self.get_setting('ARC.b.0'), 0)

    def test_can_traverse_into_list_then_dict(self):
        self.assertEqual(self.get_setting('ARC.c.0.c'), 'c')

    def test_returns_default_for_non_existent_root(self):
        default = object()
        self.assertIs(self.get_setting('NOPE', default), default)

    def test_returns_default_for_non_existent_nested_setting(self):
        default = object()
        self.assertIs(self.get_setting('ARC.nope', default), default)

    def test_raises_when_not_found_and_no_default(self):
        self.assertRaises(KeyError, self.get_setting, 'NOPE')

    def test_can_traverse_into_string_setting(self):
        self.assertEqual(self.get_setting('ARC.d.0'), 'd')

    def test_bad_index_causes_type_error(self):
        self.assertRaises(TypeError, self.get_setting, 'ARC.b.nope')


@override_settings(CAS={
    'extra': 'extra',
    'overridden': 'overridden',
})
class TestGetPrefixedSettings(SimpleTestCase):

    def setUp(self):
        super().setUp()
        defaults = {
            'base_url': 'http://example.com/cas/',
            'parent': {
                'child': 'child',
            },
            'overridden': 'default',
        }
        self.settings = PrefixedSettings('CAS', defaults)

    def test_get_from_defaults(self):
        self.assertEqual(self.settings.get('base_url'), 'http://example.com/cas/')

    def test_get_nested_from_defaults(self):
        self.assertEqual(self.settings.get('parent.child'), 'child')

    def test_get_from_project_settings(self):
        self.assertEqual(self.settings.get('extra'), 'extra')

    def test_get_setting_overridden_in_project_settings(self):
        self.assertEqual(self.settings.get('overridden'), 'overridden')

    def test_defaults_trump_passed_default(self):
        self.assertEqual(
            self.settings.get('base_url', 'http://example.com/other/'),
            'http://example.com/cas/')

    def test_passed_default_does_not_trump_project_setting(self):
        self.assertEqual(self.settings.get('extra', 'default'), 'extra')

    def test_get_default_for_nonexistent(self):
        self.assertEqual(self.settings.get('pants', 'jeans'), 'jeans')
