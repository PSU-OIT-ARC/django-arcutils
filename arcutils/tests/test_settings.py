from unittest import TestCase

from arcutils.settings import NOT_SET, SettingNotFoundError, get_setting


class Settings(object):

    pass


class TestGetSettings(TestCase):

    def setUp(self):
        settings = Settings()
        settings.ARC = {
            'a': 'a',
            'b': [0, 1],
            'c': [{'c': 'c'}],
            'd': 'd',
        }
        self.settings = settings

    def get_setting(self, key, default=NOT_SET):
        return get_setting(key, default=default, _settings=self.settings)

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
        self.assertRaises(SettingNotFoundError, self.get_setting, 'NOPE')

    def test_cannot_traverse_into_string_setting(self):
        self.assertRaises(ValueError, self.get_setting, 'ARC.d.0')

    def test_bad_index_causes_value_error(self):
        self.assertRaises(ValueError, self.get_setting, 'ARC.b.nope')
