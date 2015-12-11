from unittest import TestCase

from arcutils.registry import (
    Registry,
    RegistryKey,
    delete_registry,
    get_registries,
    get_registry,
)


class TestRegistry(TestCase):

    def setUp(self):
        self.registry_name = '__arc_test__'

    def tearDown(self):
        delete_registry(self.registry_name)

    def get_registry(self):
        return get_registry(self.registry_name)

    def test_get_registry_creates_registry(self):
        registries = get_registries()
        self.assertNotIn(self.registry_name, registries)
        self.assertIsInstance(self.get_registry(), Registry)
        self.assertIn(self.registry_name, registries)

    def test_components_must_be_registered_as_types(self):
        registry = self.get_registry()
        component = object()
        self.assertRaises(TypeError, registry.add_component, component, 'key')

    def test_adding_same_component_twice_with_same_key_is_safe(self):
        registry = self.get_registry()
        Base = type('Base', (), {})
        Type = type('Type', (Base,), {})
        instance = Type()
        added = registry.add_component(instance, Type)
        self.assertTrue(added)
        added = registry.add_component(instance, Type)
        self.assertFalse(added)

    def test_register_under_subclass(self):
        registry = self.get_registry()
        Base = type('Base', (), {})
        Type = type('Type', (Base,), {})
        instance = Type()
        # Register under subclass
        added = registry.add_component(instance, Type)
        self.assertTrue(added)
        # Fetch using subclass
        component = registry.get_component(Type)
        self.assertIs(component, instance)
        # Fetch using base class
        component = registry.get_component(Base)
        self.assertIs(component, instance)

    def test_register_under_subclass_with_name(self):
        registry = self.get_registry()
        Base = type('Base', (), {})
        Type = type('Type', (Base,), {})
        instance = Type()
        # Register under subclass with name
        added = registry.add_component(instance, Type, 'name')
        self.assertTrue(added)
        # Fetch using subclass
        component = registry.get_component(Type, 'name')
        self.assertIs(component, instance)
        # Fetch using base class
        component = registry.get_component(Base, 'name')
        self.assertIs(component, instance)
        # Name is required
        component = registry.get_component(Base)
        self.assertIsNone(component)

    def test_dict_style_access(self):
        registry = get_registry()
        Type = type('Type', (), {})
        instance = Type()
        registry[Type] = instance
        self.assertIn(Type, registry)
        self.assertIs(registry[Type], instance)
        registry[(Type, 'alt')] = instance
        self.assertIn((Type, 'alt'), registry)
        self.assertIs(registry[(Type, 'alt')], instance)

    def test_add_factory(self):
        registry = get_registry()
        Type = type('Type', (), {})
        component = Type()
        factory = lambda: component
        registry.add_factory(factory, Type)
        self.assertIs(registry._components[RegistryKey(Type)], factory)
        retrieved_component = registry.get_component(Type)
        self.assertIs(retrieved_component, component)
