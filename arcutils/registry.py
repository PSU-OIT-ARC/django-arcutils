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
from threading import RLock

from django.utils.module_loading import import_string

from .settings import get_setting


DEFAULT_REGISTRY = '{prefix}.default_registry'.format(prefix=__name__)


class RegistryError(Exception):

    pass


class ComponentExistsError(RegistryError, KeyError):

    pass


class ComponentDoesNotExistError(RegistryError, KeyError):

    pass


class RegistryKey:

    def __init__(self, type_, name=None):
        if not isinstance(type_, type):
            raise TypeError('Expected a type; got an instance of %s' % type(type_))
        self.type = type_
        self.name = name

    @classmethod
    def from_arg(cls, arg):
        if isinstance(arg, type):
            type_, name = arg, None
        elif isinstance(arg, tuple) and len(arg) == 2:
            type_, name = arg
        else:
            raise TypeError('Expected a type or a 2-tuple; got a %r instead' % arg)
        return RegistryKey(type_, name)

    def __eq__(self, other):
        return (self.type, self.name) == (other.type, other.name)

    def __hash__(self):
        return hash((self.type, self.name))

    def __repr__(self):
        return '<{0.__class__.__name__} type={0.type.__name__} name={0.name}>'.format(self)

    def __str__(self):
        return '{0.type}:{0.name}'.format(self)


class FakeLock:

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


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

    TODO: Add a ``close_registration()`` method? This would allow
          locking during the component registration phase but then allow
          unlocked access to components. It would also be a nice way to
          make a registry immutable (or at least not easily mutable).

    """

    _none = object()  # Used where None is a valid value

    def __init__(self, name,  use_locking=True, safe=True):
        self.name = name
        self._components = {}
        self._lock = RLock() if use_locking else FakeLock()
        self._safe = safe
        self._factories = set()

    def add_component(self, component, type_, name=None, safe=None):
        """Add ``component`` with key ``(type_, name)``.

        If a component has already been registered with a given key, the
        default is to do nothing--that's what ``safe`` indicates. If
        ``safe`` is ``False``, a ``ComponentExistsError`` will be raised
        instead.

        To replace a component, first remove it and then add the new
        component.

        Returns ``True`` or ``False`` indicating whether the component
        was added or not.

        """
        # Keep multiple threads from registering a component with the
        # same key at the same time.
        with self._lock:
            has_component = self.has_component(type_, name)
            key = RegistryKey(type_, name)
            if has_component:
                safe = safe if safe is not None else self._safe
                if safe:
                    return False
                else:
                    raise ComponentExistsError(key)
            self._components[key] = component
            return True

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
            self._factories.add(factory)
            return self.add_component(factory, *args, **kwargs)

    def remove_component(self, type_, name=None, safe=True):
        """Remove component with key ``(type_, name)`` if it exists.

        If no component is registered with a given key, the default is
        to do nothing--that's what ``safe`` indicates. If ``safe`` is
        ``False``, a ``ComponentDoesNotExistError`` will be raised
        instead.

        Returns ``True`` or ``False`` indicating whether the component
        was removed or not.

        """
        with self._lock:
            has_component = self.has_component(type_, name)
            key = RegistryKey(type_, name)
            if not has_component:
                if safe:
                    return False
                else:
                    raise ComponentDoesNotExistError(key)
            del self._components[key]
            return True

    def get_component(self, type_, name=None, default=None):
        with self._lock:
            component = self._find_component(type_, name)
            component = self._factory_to_component(component, type_, name)
            return default if component is self._none else component

    def has_component(self, type_, name=None):
        with self._lock:
            return self._find_component(type_, name) is not self._none

    def _factory_to_component(self, obj, type_, name):
        if obj in self._factories:
            self._factories.remove(obj)
            obj = obj()
            self._components[RegistryKey(type_, name)] = obj
        return obj

    def _find_component(self, type_, name=None):
        """Find ``component`` with key ``(type_, name)``."""
        key = RegistryKey(type_, name)
        if key in self._components:
            return self._components[key]
        # Try to find a component registered as a subclass of type_.
        for k in self._components.keys():
            if issubclass(k.type, type_) and k.name == name:
                return self._components[k]
        return self._none

    def items(self):
        return self._components.items()

    def __contains__(self, arg):
        arg = RegistryKey.from_arg(arg)
        return self.has_component(arg.type, arg.name)

    def __getitem__(self, arg):
        key = RegistryKey.from_arg(arg)
        component = self.get_component(key.type, key.name, self._none)
        if component is self._none:
            raise ComponentDoesNotExistError(key)
        return component

    def __setitem__(self, arg, component):
        arg = RegistryKey.from_arg(arg)
        self.add_component(component, arg.type, arg.name)

    def __iter__(self):
        return iter(self._components)

    def __str__(self):
        s = []
        with self._lock:
            for k, v in self.items():
                v = self._factory_to_component(v, k.type, k.name)
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

    """
    registries = get_registries()
    with _registry_lock:
        if name in registries:
            return registry_type[name]
        if registry_type is None:
            registry_type = get_setting('ARC.registry.type', Registry)
        if isinstance(registry_type, str):
            registry_type = import_string(registry_type)
        registries[name] = registry_type(name, **kwargs)
        return registries[name]


def delete_registry(name) -> None:
    registries = get_registries()
    with _registry_lock:
        if name in registries:
            del registries[name]


class RegistryMiddleware:

    """Attaches the default component registry to the current request.

    Add this to MIDDLEWARE_CLASSES for easy access to the registry from
    views.

    By default, this sets ``request.registry`` to point at the registry.
    Set the ``ARC.registry.request_attr_name`` setting to change this to
    something else (e.g., in case of a name clash).

    You can also use the registry in other middleware that comes after
    this middleware.

    """

    def process_request(self, request):
        name = get_setting('ARC.registry.request_attr_name', 'registry')
        setattr(request, name, get_registry())
