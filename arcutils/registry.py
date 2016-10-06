"""Component registry.

A component registry is useful when you want to stash global utilities
somewhere (e.g., like a connection pool). It's a bit more sophisticated
than just stashing things in your project's settings (ew) or as module
globals (double ew).

The primary exports from this module are:

    - :func:`get_registry`: Get the registry so you can stash stuff in
      it or get stuff from it.
    - :class:`RegistryMiddleware`: Provides easy access to the registry
      in views via ``request.registry``.

A typical setup involves creating a top level ``apps`` module in your
project with a Django app config class like this::

    from django.apps import AppConfig
    from arcutils.registry import get_registry

    class ComponentRegistryConfig(AppConfig):

        name = 'quickticket'

        def ready(self):
            registry = get_registry()
            registry.add_component(component, type, name)
            ...

"""
from collections import namedtuple
from threading import Lock, RLock

from django.utils.module_loading import import_string

from .middleware import MiddlewareBase
from .settings import PrefixedSettings
from .types import Option, Some, Null


DEFAULT_REGISTRY = '{prefix}.default_registry'.format(prefix=__name__)


settings = PrefixedSettings('ARC')


class RegistryError(Exception):

    pass


class RegistryClosedError(RegistryError):

    pass


class ComponentExistsError(RegistryError, KeyError):

    pass


class ComponentDoesNotExistError(RegistryError, KeyError):

    pass


FoundComponent = namedtuple('FoundComponent', ('key', 'component'))


class RegistryKey(namedtuple('RegistryKey', ('type', 'name'))):

    __slots__ = ()

    def __new__(cls, type_, name=None):
        if not isinstance(type_, type):
            raise TypeError('Expected a type; got an instance of {0.__class__}'.format(type_))
        return super().__new__(cls, type_, name)

    @classmethod
    def from_arg(cls, arg):
        if isinstance(arg, type):
            type_, name = arg, None
        elif isinstance(arg, tuple) and len(arg) == 2:
            type_, name = arg
        else:
            raise TypeError('Expected a type or a 2-tuple; got a %r instead' % arg)
        return RegistryKey(type_, name)


class FakeLock:

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ComponentFactory:

    def __init__(self, factory):
        # None is potentially a valid component value, so we use an
        # Option here.
        self.component = Null
        self.factory = factory
        self.lock = Lock()

    def __call__(self):
        # This needs to be atomic so that two threads don't attempt to
        # materialize this factory at the same time, which could lead to
        # the component being created twice, which could be problematic
        # in some cases.
        with self.lock:
            if not self.component:
                self.component = Some(self.factory())
        return self.component.unwrap()


class Registry:

    """A component registry where components are registered by type.

    Components are registered by a type (i.e., a class) and, optionally,
    a name. For example, two LDAP connections could be registered like
    this in an app's startup code::

        import django.apps

        from ldap3 import Connection

        from arcutils.registry import get_registry

        class SomeAppConfig(django.apps.AppConfig):

            def ready():
                registry = get_registry(use_locking=False)  # Get the default registry
                ldap_connection = Connection(...)  # OIT LDAP connection
                ad_connection = Connection(...)  # AD connection
                registry.add_component(ldap_connection, Connection, 'default')
                registry.add_component(ad_connection, Connection, 'ad')

    And then we get a hold of those connections in app code (e.g., in
    a view) like this::

        from arcutils.registry import get_registry

        def ad_search_view(request, search_term):
            registry = get_registry()
            cxn = registry.get_component(ldap3.Connection, 'ad')
            cxn.search(search_term)
            ...

    By default, all registry operations hold a common lock so that
    components can be safely added and removed. In the case where
    component registration happens in an already-locked scope (as is the
    case when Django calls ``AppConfig.ready()``) and components won't be
    removed (which would typically be a very rare operation), locking
    isn't necessary, and the ``use_locking`` flag can be set to
    ``False`` to avoid locking, which may be beneficial to performance
    in some cases.

    To make a registry immutable(ish) after all components have been
    registered, call :meth:`close_registration`. This allows for locking
    in the component registration phase while allowing for concurrent,
    un(b)locked access to components in application code.

    When registration is closed, all mutating methods will raise a
    :exc:`RegistryClosedError`. Further attempts to close registration
    will also raise such an error.

    .. note:: Closing registration is experimental and needs tests.

    """

    def __init__(self, name, use_locking=True):
        self.name = name
        self._components = {}
        self._lock = RLock() if use_locking else FakeLock()
        self._open = True

    def add_component(self, component, type_, name=None, replace=False):
        """Add ``component`` with key ``(type_, name)``.

        If a component has already been registered with a given key, the
        default is to raise a ``ComponentExistsError``. Pass
        ``replace=True`` to replace an existing component.

        When a component is successfully added, it will be returned
        (since that seems more useful than returning nothing).

        """
        # Keep multiple threads from registering a component with the
        # same key at the same time.
        with self._lock, self._find_component(type_, name) as option:
            key = RegistryKey(type_, name)
            if option and not replace:
                raise ComponentExistsError(key)
            self._components[key] = component
            return component

    def add_factory(self, factory, *args, **kwargs):
        """Provides a lazy way to instantiate a component.

        This is used to mark a callable as a component factory. The
        factory won't be called to instantiate the component until the
        first time the component is retrieved from the registry.

        .. note:: Factory callables are not passed any args.

        After marking the factory as such, :meth:`.add_component` is
        called to add the factory as a component in the usual way.

        """
        with self._lock:
            return self.add_component(ComponentFactory(factory), *args, **kwargs)

    def remove_component(self, type_, name=None, default=ComponentDoesNotExistError):
        """Remove component with key ``(type_, name)`` if it exists.

        Returns the removed component, or ``default`` if the component
        doesn't exist.

        If the component doesn't exist and no ``default`` is passed, a
        :exc:`ComponentDoesNotExistError` will be raised.

        """
        if default is ComponentDoesNotExistError:
            default = ComponentDoesNotExistError(RegistryKey(type_, name))
        with self._lock, self._find_component(type_, name) as option:
            return option.and_(lambda v: Some(self._components.pop(v.key))).unwrap(lambda: default)

    def get_component(self, type_, name=None, default=None):
        with self._lock, self._find_component(type_, name) as option:
            return option(
                some=lambda v: self._factory_to_component(v.component, v.key),
                null=lambda: default
            )

    def has_component(self, type_, name=None):
        with self._lock, self._find_component(type_, name) as option:
            return option(some=lambda v: True, null=lambda: False)

    def close_registration(self):
        """Close registration (disallow adding & removing of components).

        XXX: This is experimental
        TODO: Write tests

        """
        with self._lock:
            if not self._open:
                raise RegistryClosedError(
                    'Cannot close registration for {0.name}: already closed'.format(self))
            self._open = False
            self.add_component = self._registration_closed
            self.add_factory = self._registration_closed
            self.remove_component = self._registration_closed
            if not isinstance(self._lock, FakeLock):
                self._lock = FakeLock()

    def _registration_closed(self, *args, **kwargs):
        raise RegistryClosedError(
            'Registration has been closed for {0.name}, '
            'so you can no longer add or remove components'
            .format(self)
        )

    def _factory_to_component(self, obj, key):
        """Materialize ``obj`` to component if ``obj`` is a factory.

        If ``obj`` is a :class:`ComponentFactory`, materialize it to a
        component by calling its factory then replacing the factory with
        the component in the registry. The materialized component is
        then returned.

        Otherwise, return ``obj`` directly.

        """
        if isinstance(obj, ComponentFactory):
            # NOTE: The call to obj blocks while the component is being
            #       created, which keeps the component from being
            #       created twice.
            obj = self._components[key] = obj()
        return obj

    def _find_component(self, type_, name=None) -> Option:
        """Find component with key ``(type_, name)``.

        If a component isn't found with that exact key, we look for a
        component registered as a subclass of ``type_`` with ``name``.
        So if a component was registered under ``(dict, 'my_stuff')``,
        ``_find_component(object, 'my_stuff')`` will find it.

        If a component is found, a wrapped :class:`FoundComponent` will
        be returned (which consists of the key where the component was
        found along with the component itself).

        """
        key = RegistryKey(type_, name)
        if key in self._components:
            return Some(FoundComponent(key, self._components[key]))
        # Try to find a component registered as a subclass of type_.
        for k in self._components.keys():
            if issubclass(k.type, type_) and k.name == name:
                return Some(FoundComponent(k, self._components[k]))
        return Null

    def items(self):
        return self._components.items()

    def __bool__(self):
        return bool(self._components)

    def __contains__(self, arg):
        arg = RegistryKey.from_arg(arg)
        return self.has_component(arg.type, arg.name)

    def __getitem__(self, arg):
        key = RegistryKey.from_arg(arg)
        return self.get_component(key.type, key.name, ComponentDoesNotExistError(key))

    def __setitem__(self, arg, component):
        arg = RegistryKey.from_arg(arg)
        self.add_component(component, arg.type, arg.name)

    def __delitem__(self, arg):
        arg = RegistryKey.from_arg(arg)
        self.remove_component(arg.type, arg.name)

    def __iter__(self):
        return iter(self._components)

    def __str__(self):
        s = []
        with self._lock:
            for k, v in self.items():
                v = self._factory_to_component(v, k)
                s.append('{k.type!r}, {k.name!r} => {v!r}'.format(k=k, v=v))
        return '\n'.join(s)


_registries = {}
_registry_lock = RLock()


def get_registries() -> dict:
    """Get the dict of registries."""
    return _registries


def get_registry(name=DEFAULT_REGISTRY, **add_kwargs) -> Registry:
    """Get the component registry indicated by ``name``.

    It will be created first if necessary.

    This will return the default registry by default, which in most
    cases is what you want. Use of multiple registries is useful in
    testing.

    The registry is a :class:`.Registry` by default. An alternative
    registry type can be specified via the ``ARC.registry.type'``
    setting, which must implement the same interface as
    :class:`Registry`.

    """
    registries = get_registries()
    with _registry_lock:
        return registries[name] if name in registries else add_registry(name, **add_kwargs)


def add_registry(name, registry_type=None, **kwargs) -> Registry:
    """Add a new registry under ``name``.

    Generally, you wouldn't call this directly from within project code.
    In most cases, you will only use :func:`.get_registry`.

    .. note:: If you add a registry with the same name as an existing
              registry, the existing registry will be replaced with the
              new registry.

    """
    registries = get_registries()
    with _registry_lock:
        if registry_type is None:
            registry_type = settings.get('registry.type', Registry)
        if isinstance(registry_type, str):
            registry_type = import_string(registry_type)
        registries[name] = registry_type(name, **kwargs)
        return registries[name]


def delete_registry(name) -> None:
    registries = get_registries()
    with _registry_lock:
        if name in registries:
            del registries[name]


class RegistryMiddleware(MiddlewareBase):

    """Attaches the default component registry to the current request.

    Add this to a project's middleware for easy access to the registry
    from views.

    By default, this sets ``request.registry`` to point at the registry.
    Set the ``ARC.registry.request_attr_name`` setting to change this to
    something else (e.g., in case of a name clash).

    You can also use the registry in other middleware that comes after
    this middleware.

    """

    def before_view(self, request):
        name = settings.get('registry.request_attr_name', 'registry')
        setattr(request, name, get_registry())
