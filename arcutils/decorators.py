class cached_property:

    """Similar to @property but caches value on first access.

    When the property is first accessed, its value is computed and set
    as an instance attribute (i.e., in the instance's ``__dict__``).
    Subsequent accesses will get the value directly from the instance's
    ``__dict__`` (i.e., this descriptor will not be invoked).

    The property can be set and deleted as usual. When the property is
    deleted, its value will be recomputed and re-set on the next access.

    Cached properties can be specified with dependencies::

        class MyType(CachedPropertyInvalidatorMixin):

            def __init__(self, thing):
                self.thing = thing

            @cached_property('thing')
            def dependent(self):
                return something if self.thing else something_else

            def elsewhere(self, new_thing):
                # This will cause the dependent property to be deleted
                # an recomputed next time it's accessed.
                self.thing = new_thing

    .. note:: This example uses :class:`CachedPropertyInvalidatorMixin`
              to take care of invalidation; specifying dependencies in
              and of itself does nothing except record the dependencies
              internally on the property instance.

    """

    def __init__(self, fget_or_dependency, *dependencies):
        # This handles all of these cases:
        #
        # 1. @cached_property
        # 2. @cached_property('dependency', ...)
        # 3. cached_property(method)
        # 4. cached_property(method, 'dependency', ...)
        # 5. cached_property('dependency', ...)(method)
        if callable(fget_or_dependency):
            self._set_fget(fget_or_dependency)
        else:
            dependencies = (fget_or_dependency,) + dependencies
        if dependencies:
            if all(isinstance(item, str) for item in dependencies):
                self.dependencies = set(dependencies)
            else:
                raise TypeError('@cached_property dependencies must be strings', dependencies)
        else:
            self.dependencies = dependencies

    def __call__(self, fget):
        # This will be invoked only when a cached_property has
        # dependencies.
        self._set_fget(fget)
        return self

    def __get__(self, obj, cls=None):
        if obj is None:  # property accessed via class
            return self
        obj.__dict__[self.__name__] = self.fget(obj)
        return obj.__dict__[self.__name__]

    def _set_fget(self, fget):
        self.fget = fget
        self.__name__ = fget.__name__
        self.__doc__ = fget.__doc__


class CachedPropertyInvalidatorMixin:

    """Mixin for classes that have cached properties with dependencies.

    Provides automatic invalidation of cached properties when one of
    their dependencies is set or deleted.

    """

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self._invalidate_cached_properties_dependent_on(name)

    def __delattr__(self, name):
        super().__delattr__(name)
        self._invalidate_cached_properties_dependent_on(name)

    @cached_property
    def _cached_properties_with_dependencies(self):
        cached_properties = {}
        for name, attr in vars(self.__class__).items():
            if isinstance(attr, cached_property) and attr.dependencies:
                cached_properties[name] = attr
        return cached_properties

    def _invalidate_cached_properties_dependent_on(self, dependency):
        for name, prop in self._cached_properties_with_dependencies.items():
            if dependency in prop.dependencies:
                # Note: We don't use hasattr(self, name) here because
                # using hasattr would cause the property to be computed.
                try:
                    delattr(self, name)
                except AttributeError:
                    pass
