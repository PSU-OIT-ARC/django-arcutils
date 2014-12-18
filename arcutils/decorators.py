class cached_property:

    """Similar to @property but caches value on first access.

    When the property is first accessed, its value is computed and set
    as an instance attribute (i.e., in the instance's ``__dict__``).
    Subsequent accesses will get the value directly from the instance's
    ``__dict__`` (i.e., this descriptor will not be invoked).

    The property can be set and deleted as usual. When the property is
    deleted, its value will be recomputed and re-set on the next access.

    """

    def __init__(self, fget):
        self.fget = fget
        self.__name__ = fget.__name__
        self.__doc__ = fget.__doc__

    def __get__(self, obj, cls=None):
        if obj is None:  # property accessed via class
            return self
        obj.__dict__[self.__name__] = self.fget(obj)
        return obj.__dict__[self.__name__]
