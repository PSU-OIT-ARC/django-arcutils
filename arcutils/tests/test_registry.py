from unittest import TestCase

from arcutils.registry import (
    ComponentFactory,
    Registry,
    RegistryKey,
    ComponentExistsError,
    ComponentDoesNotExistError,
    add_registry,
    delete_registry,
    get_registries,
    get_registry,
)


class RegistryTestCase(TestCase):

    def setUp(self):
        self.registry_name = '__arc_test__'

    def tearDown(self):
        delete_registry(self.registry_name)

    def get_registries(self):
        return get_registries()

    def add_registry(self, name=None):
        return add_registry(name or self.registry_name)

    def get_registry(self, name=None):
        return get_registry(name or self.registry_name)


class TestRegistries(RegistryTestCase):

    def test_get_registry_creates_registry(self):
        self.assertNotIn(self.registry_name, self.get_registries())
        registry = self.get_registry()
        self.assertIn(self.registry_name, self.get_registries())
        self.assertIsInstance(registry, Registry)

    def test_getting_the_same_registry_multiple_times_returns_the_same_registry(self):
        registries = get_registries()
        self.assertNotIn(self.registry_name, registries)
        registry = self.get_registry()
        self.assertIs(self.get_registry(), registry)

    def test_adding_a_registry_with_the_name_of_an_existing_registry_replaces_the_original(self):
        registries = get_registries()
        self.assertNotIn(self.registry_name, registries)
        registry = self.add_registry(self.registry_name)
        self.assertIsNot(self.add_registry(self.registry_name), registry)


class TestRegistry(RegistryTestCase):

    def test_components_must_be_registered_as_types(self):
        registry = self.get_registry()
        component = object()
        self.assertRaises(TypeError, registry.add_component, component, 'key')

    def test_adding_a_component_returns_the_component(self):
        registry = self.get_registry()
        Base = type('Base', (), {})
        Type = type('Type', (Base,), {})
        instance = Type()
        component = registry.add_component(instance, Type)
        self.assertIs(component, instance)

    def test_replacing_a_component_removes_it_and_adds_and_returns_the_new_component(self):
        registry = self.get_registry()
        instance_1 = object()
        registry[object] = instance_1
        self.assertIs(registry[object], instance_1)
        instance_2 = object()
        registry.add_component(instance_2, object, replace=True)
        self.assertIs(registry[object], instance_2)

    def test_adding_the_same_component_twice_with_same_key_causes_an_error(self):
        registry = self.get_registry()
        Type = type('Type', (), {})
        instance = Type()
        registry.add_component(instance, Type)
        self.assertRaises(ComponentExistsError, registry.add_component, instance, Type)

    def test_removing_a_component_removes_and_returns_the_component(self):
        registry = self.get_registry()
        components = registry._components
        Type = type('Type', (), {})
        component = Type()
        self.assertNotIn(RegistryKey(Type), components)
        self.assertNotIn(Type, registry)
        registry[Type] = component
        self.assertIn(RegistryKey(Type), components)
        self.assertIn(Type, registry)
        obj = registry.remove_component(Type)
        self.assertIs(obj, component)
        self.assertNotIn(RegistryKey(Type), components)
        self.assertNotIn(Type, registry)

    def test_removing_a_nonexistent_component_raises_an_error(self):
        registry = self.get_registry()
        self.assertRaises(ComponentDoesNotExistError, registry.remove_component, object)

    def test_removing_a_nonexistent_component_returns_passed_default(self):
        registry = self.get_registry()
        default = object()
        component = registry.remove_component(object, default=default)
        self.assertIs(component, default)

    def test_removing_a_component_using_dict_syntax(self):
        registry = self.get_registry()
        self.assertNotIn(object, registry)
        registry[object] = object()
        self.assertIn(object, registry)
        del registry[object]
        self.assertNotIn(object, registry)

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
        component_factory = registry._components[RegistryKey(Type)]
        self.assertIsInstance(component_factory, ComponentFactory)
        self.assertIs(component_factory.factory, factory)
        retrieved_component = registry.get_component(Type)
        self.assertIs(retrieved_component, component)
