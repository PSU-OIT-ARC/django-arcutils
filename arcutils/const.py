"""Constants."""


# A ``None``-ish constant for use where ``None`` may be a valid value.
NOT_SET = type('NOT_SET', (), {
    '__bool__': (lambda self: False),
    '__str__': (lambda self: 'NOT_SET'),
    '__repr__': (lambda self: 'NOT_SET'),
    '__copy__': (lambda self: self),
})()

# An alias for NOT_SET that may be more semantically-correct in some
# contexts.
NO_DEFAULT = NOT_SET
