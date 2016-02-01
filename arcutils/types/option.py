class Option:

    """Used to unambiguously indicate the presence of a value.

    There are many cases where ``None`` is a valid value in the
    application domain, so ``None`` can't be used to unambiguously
    indicate that a value does not exist for a given key or name.

    We often end up creating *really None* objects to work around this::

        NO_DEFAULT = object()

        class MyStuff:

            def __init__(self):
                self.stuff = {}

            def get(self, key, default=NO_DEFAULT):
                v = self.stuff.get(key, default)
                if v is NO_DEFAULT:
                    raise KeyError(key)  # Or do something else
                return v

        my_stuff = MyStuff()
        v = my_stuff.get('key')  # Explodes if key isn't present
        v = my_stuff.get('key', default=None)  # None if key isn't present

    But that pattern is tedious and ad hoc (often introducing semantic
    twists like ``default is not NO_DEFAULT``).

    The :class:`Option` type provides an alternative to that pattern.
    It's intended to be more intuitive with a nicer API. And also, it's
    fun, so what the heck... why not?

    :class:`Some` is used to indicate the presence of a valid value
    while :const:`Null` is used to indicate the lack of a valid value.

    As an example, let's take a look at the standard ``dict.get()``
    method. We often run into a situation like this::

        d = dict(...)
        v = d.get('key')  # d['key'] is None OR d['key'] isn't present

    In other words, when ``dict.get()`` returns ``None``, we can't tell
    if the key wasn't present or if it was present and had the value
    ``None``.

    Instead, we can imagine ``dict.get()`` working like this::

        d = dict(...)
        option = d.get('key')  # -> Some(d['key']) OR Null
        if option:
            value = option.unwrap()
        else:
            ...

    Now we can tell with certainty whether the key was present. Note
    that the bool value of an :class:`Option` is independent of the
    value it contains (*any* :class:`Some` is *always* ``True`` and, of
    course, :const:`Null` is always ``False``).

    If we want a default of ``None`` when a key isn't present, we could
    do this with our hypothetical option-returning ``dict.get()``::

        option = d.get('key', default=None)  # Some(d['key']) OR Some(None)
        value = option.unwrap()

    Here we've sidestepped the question of whether or not the key is
    present because there's no ambiguity.

    """

    def __init__(self, value):
        self.value = value

    # Context manager interface; provides a syntax block but no
    # additional functionality

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        return False

    # Methods that return a bool

    def is_some(self):
        return isinstance(self, Some)

    __bool__ = is_some

    def is_null(self):
        return self is Null

    # Methods that run an action then return the original Option

    def and_do(self, action):
        """Do ``action()`` if :class:`Some`; always return ``self``.

        If ``self`` is a :class:`Some`, ``action`` will be called with
        :attr:`value` unless ``action`` is an exception, in which case
        it will be raised directly.

        The return value of ``action`` will be discarded unless it's an
        exception, in which case it will be raised.

        If ``self`` is :const:`Null`, ``action`` will not be called.

        Always return ``self`` unless an exception is raised.

        """
        if self:
            raise_or_call_and_return(action, self.value)
        return self

    def or_do(self, action):
        """Do ``action()`` if :const:`Null`; always return ``self``.

        If ``self`` is :const:`Null`, ``action`` will be called with no
        args unless ``action`` is an exception, in which case it will
        be raised directly.

        The return value of ``action`` will be discarded unless it's an
        exception, in which case it will be raised.

        If ``self`` is a :class:`Some`, ``action`` will not be called.

        Always return ``self`` unless an exception is raised.

        """
        if not self:
            raise_or_call_and_return(action)
        return self

    # Methods that unwrap an Option and return a value

    def unwrap(self, default=None):
        """Return value if :class:`Some`; else return ``default()``.

        If ``default`` is an exception, it will be raised directly. If
        ``default()`` returns an exception, that exception will be
        raised.

        """
        if self:
            return raise_or_return(self.value)
        if default is None:
            raise TypeError('Cannot unwrap Null')
        return raise_or_call_and_return(default)

    def __call__(self, some=lambda v: v, null=lambda: Null):
        """Resolve the value of an :class:`Option`.

        By default, this will return :attr:`value` if this is a
        :class:`Some` or :const:`Null` if this is :const:`Null`.

        If ``some`` is passed, it will be called with :attr:`value` if
        ``self`` is a :class:`Some`. If ``some`` is or returns an
        exception, that exception will be raised.

        If ``null`` is passed, it will be called with no args if ``self``
        is :const:`Null`. If ``null`` is or returns an exception, that
        exception will be raised.

        The idea behind this is to provide a nice syntax that sort-of
        looks like pattern matching in languages like Rust.

        Usage::

            with returns_option() as option:
                option(
                    some=lambda v: do_something_with_v(v),
                    null=lambda: default
                )

        """
        if self:
            return raise_or_call_and_return(some, self.value)
        return raise_or_call_and_return(null)

    # Methods that may return the original Option or a different one

    def or_(self, default):
        """Return ``self`` if it's a :class:`Some` else ``default``.

        ``default`` can be...

        - an :class:`Option`
        - an exception, which will be raised directly
        - a callable that takes no args & returns an :class:`Option`
        - a callable that takes no args & returns an exception, which
          will be raised

        """
        if self:
            return self
        raise_or_return(default)
        if isinstance(default, Option):
            return default
        option = raise_or_return(default())
        if not isinstance(option, Option):
            raise TypeError('default must return an Option')
        return option

    def and_(self, instead):
        """Return ``self`` if it's :const:`Null` else ``instead(self.value)``.

        ``instead`` can be...

        - an :class:`Option`
        - an exception, which will be raised directly
        - a callable that takes one arg & returns an :class:`Option`
        - a callable that takes one & returns an exception, which
          will be raised

        """
        if not self:
            return self
        raise_or_return(instead)
        if isinstance(instead, Option):
            return instead
        option = raise_or_return(instead(self.value))
        if not isinstance(option, Option):
            raise TypeError('instead must return an Option')
        return option

    def __str__(self):
        return 'Some({0.value!r})'.format(self) if self else 'Null'


Some = type('Some', (Option,), {})
Null = type('Null', (Option,), {})(None)


def raise_or_return(value):
    """Raise ``value`` if it's an exception; else return it."""
    is_exc = isinstance(value, BaseException)
    is_exc = is_exc or (isinstance(value, type) and issubclass(value, BaseException))
    if is_exc:
        raise value
    return value


def raise_or_call_and_return(callable_, *args, **kwargs):
    """Raise ``callable_`` if it's an exception; else call it.

    The result of ``callable_(*args, **kwargs)`` will be returned unless
    the result is an exception, in which case the result will be raised.

    """
    callable_ = raise_or_return(callable_)
    return raise_or_return(callable_(*args, **kwargs))
