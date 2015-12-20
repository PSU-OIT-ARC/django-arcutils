from collections import defaultdict
from unittest import TestCase

from arcutils.decorators import cached_property, CachedPropertyInvalidatorMixin


class TestCachedProperty(TestCase):

    def setUp(self):

        class Type(CachedPropertyInvalidatorMixin):

            def __init__(self):
                self.attr = object()
                self.thing = object()

            @cached_property
            def prop(self):
                counts['prop'] += 1
                return values['prop']

            @cached_property('attr')
            def prop_with_dep(self):
                counts['prop_with_dep'] += 1
                return values['prop_with_dep']

            def prop_with_deps(self):
                counts['prop_with_deps'] += 1
                return values['prop_with_deps']

            prop_with_deps = cached_property(prop_with_deps, 'attr', 'thing')

            @cached_property('prop')
            def prop_with_prop_dep(self):
                counts['prop_with_prop_dep'] += 1
                return values['prop_with_prop_dep']

        self.Type = Type
        counts = self.counts = defaultdict(int)
        values = self.values = defaultdict(lambda: object())

    def test_cached_property(self):
        t = self.Type()
        name = 'prop'
        self.assertIsInstance(getattr(t.__class__, name), cached_property)
        self.assertEqual(self.counts[name], 0)
        # First access computes value
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 1)
        # Subsequent access returns computed value directly
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 1)

    def test_cached_property_with_one_dep(self):
        t = self.Type()
        name = 'prop_with_dep'
        self.assertIsInstance(getattr(t.__class__, name), cached_property)
        self.assertEqual(self.counts[name], 0)
        # First access computes value
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 1)
        # Subsequent access returns computed value directly
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 1)
        # Setting a dependency causes the value to be recomputed
        t.attr = object()
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 2)
        # Deleting a dependency causes the value to be recomputed
        del t.attr
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 3)

    def test_cached_property_with_dep_that_is_a_cached_property(self):
        t = self.Type()
        name = 'prop_with_prop_dep'
        self.assertIsInstance(getattr(t.__class__, name), cached_property)
        self.assertEqual(self.counts[name], 0)
        # First access computes value
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 1)
        # Subsequent access returns computed value directly
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 1)
        # Setting a dependency causes the value to be recomputed
        t.prop = object()
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 2)
        # Deleting a dependency causes the value to be recomputed
        del t.prop
        self.assertIs(getattr(t, name), self.values[name])
        self.assertEqual(self.counts[name], 3)
