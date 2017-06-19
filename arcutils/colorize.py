"""Colorize strings for output to terminal.

Typical usage looks like this::

    >>> from arcutils.colorize import colorizer, printer
    >>> colorized_string = colorizer.error('Whoops')
    >>> colorized_string
    '\\x1b[91mWhoops\\x1b[0m'
    >>> print(colorized_string)
    \x1b[91mWhoops\x1b[0m
    >>> printer.error('Something bad happened')
    Something bad happened

You can also do some more advanced things like this::

    from arcutils.colorize import colorizer, RED, GREEN, BLUE
    my_string = colorizer(RED, 'red', GREEN, 'green', BLUE, 'blue')
    print(my_string)

If you need to, you can customize the colors used by creating an
instance of :class:`.Colorizer` or :class:`ColorPrinter` with your own
color map.

"""
import os
import sys


class Color:

    def __init__(self, name, code):
        self.name = name
        self.code = code

    def __str__(self):
        return self.code

    def __repr__(self):
        return '<Color: {0.name}>'.format(self)


NONE = Color('none', '')
RESET = Color('reset', '\033[0m')
RED = Color('red', '\033[91m')
GREEN = Color('green', '\033[92m')
YELLOW = Color('yellow', '\033[93m')
BLUE = Color('blue', '\033[94m')
MAGENTA = Color('magenta', '\033[95m')


# Map symbolic names to colors
COLOR_MAP = {
    'none': NONE,
    'reset': RESET,
    'header': MAGENTA,
    'info': BLUE,
    'success': GREEN,
    'warning': YELLOW,
    'error': RED,
    'danger': RED,
}


class _Base:

    def __new__(cls, color_map=None):
        """Dynamically generate convenience methods.

        All we're doing here is dynamically generating the convenience
        methods .info(), .error(), etc. These names correspond to the
        keys of the instance's color map.

        Each subclass of _Base must point its ``__call__`` method at its
        main implementation method. E.g. :class:`Colorizer` points its
        ``__call__`` method at its ``colorize`` method.

            >>> colorizer.info.__name__
            'info'
            >>> colorizer.info.__doc__
            'info convenience method'
            >>> another_colorizer = Colorizer({'pants': ''})
            >>> another_colorizer.pants.__name__
            'pants'
            >>> hasattr(colorizer, 'pants')
            False

        """
        names = set(COLOR_MAP.keys())
        if color_map is not None:
            names.update(color_map.keys())
        # Create a subclass so instances created later don't affect
        # instances created earlier. Without this, if an instance was
        # created with, e.g., an extra color map entry, instances
        # created earlier would get a new convenience method, which
        # wouldn't be the worst thing in the world, but it might cause
        # confusion.
        sub_cls = type(cls.__name__, (cls,), {})
        for name in names:
            setattr(sub_cls, name, cls.__make_convenience_method(name))
        return super(_Base, cls).__new__(sub_cls)

    @classmethod
    def __make_convenience_method(cls, name):
        def method(self, *args, **kwargs):
            kwargs['color'] = name
            return self(*args, **kwargs)
        method.__name__ = name
        method.__doc__ = '{name} convenience method'.format(name=name)
        return method

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Colorizer(_Base):

    """Colorize strings.

    Default colors can be overridden by passing a color map to the
    constructor.

    Examples::

        >>> colorizer = Colorizer({'success': YELLOW, 'special': GREEN})
        >>> colorizer.colorize('boring old message')
        'boring old message\\x1b[0m'
        >>> colorizer.colorize('boring old message', color='none')
        'boring old message\\x1b[0m'
        >>> colorizer.colorize(NONE, 'boring old message')
        'boring old message\\x1b[0m'
        >>> colorizer.colorize(RED, 'red', GREEN, 'green', BLUE, 'blue')
        '\\x1b[91mred \\x1b[92mgreen \\x1b[94mblue\\x1b[0m'
        >>> colorizer.info('check this out')
        '\\x1b[94mcheck this out\\x1b[0m'
        >>> colorizer.error('whoopsie')
        '\\x1b[91mwhoopsie\\x1b[0m'
        >>> colorizer.success('success is green by default, but it was overridden')
        '\\x1b[93msuccess is green by default, but it was overridden\\x1b[0m'
        >>> colorizer.special('special')
        '\\x1b[92mspecial\\x1b[0m'

    """

    def __init__(self, color_map=None):
        self.color_map = COLOR_MAP.copy()
        if color_map is not None:
            self.color_map.update(color_map)

    def colorize(self, *args, sep=' ', end='', reset=True, **kwargs):
        """Returns a colorized string (joining ``args`` into one str).

        Pass ``color`` as a keyword arg to colorize ``*args``. It can
        be a name from the color map ('info', 'error', etc) or it can be
        an instance of :class:`Color`.

        Alternatively, you can pass one or more :class:`Color`s as
        args; the output string will change color each time a new color
        is encountered in args. If the ``color`` keyword arg is also
        passed, the output string will start with the specified color.

        The remaining args are similar to the built-in ``print()``
        function. ``sep`` is a space as usual; ``end`` is an empty
        string instead of a newline.

        The string is terminated with the terminal reset code unless
        ``reset=False``.

        """
        color = kwargs.get('color', NONE)
        if not isinstance(color, Color):
            color = self.color_map[color]
        args = (color,) + args
        string = []
        for arg in args[:-1]:
            if isinstance(arg, Color):
                string.append(str(arg))
            else:
                string.append(str(arg))
                string.append(sep)
        string.append(str(args[-1]))
        string = ''.join(string)
        reset = self.color_map['reset'] if reset else ''
        string = '{string}{end}{reset}'.format(**locals())
        return string

    __call__ = colorize


class ColorPrinter(_Base):

    """Print things in color.

    Default colors can be overridden by passing a color map to the
    constructor. When the output device isn't a TTY, colorizing is
    disabled.

    Examples::

        >>> printer = ColorPrinter()
        >>> printer.print('boring old message')
        boring old message
        >>> printer('boring old message')
        boring old message
        >>> printer.info('check this out')
        check this out
        >>> printer.error('whoopsie')
        whoopsie

    Note: This uses the print function from Python 3.

    """

    def __init__(self, color_map=None):
        self.colorizer = Colorizer(color_map)

    def print(self, *args, **kwargs):
        """Like built-in ``print()`` but colorizes strings.

        Pass ``color`` as a keyword arg to colorize ``*args`` before
        printing them. If no ``color`` is passed or if ``file`` is not
        a TTY, *args will printed without color.

        See :meth:`Colorizer.colorize` for more info on how colorization
        works and advanced colorization options.

        """
        color = kwargs.pop('color', NONE)
        file = kwargs.get('file', sys.stdout)
        try:
            is_a_tty = file.isatty()
        except AttributeError:
            is_a_tty = False
        if is_a_tty:
            colorizer_kwargs = kwargs.copy()
            colorizer_kwargs['color'] = color
            colorizer_kwargs.pop('file', None)
            colorizer_kwargs.setdefault('end', os.linesep)
            string = self.colorizer.colorize(*args, **colorizer_kwargs)

            print_kwargs = kwargs.copy()
            print_kwargs.pop('sep', None)
            print_kwargs['end'] = ''
            print(string, **print_kwargs)
        else:
            args = [a for a in args if not isinstance(a, Color)]
            print(*args, **kwargs)

    __call__ = print


# Default public API
colorizer = Colorizer()
printer = ColorPrinter()


if __name__ == '__main__':
    # A basic demonstration

    print(colorizer.header('Using print() to print colorized strings:'))
    print(colorizer(RED, 'red', GREEN, 'green', BLUE, 'blue'))
    print(colorizer.info('Some info'))
    print(colorizer.warning('I don\'t know about that...'))
    print(colorizer.success('Achievement unlocked :)'))
    print(colorizer.error('Something bad happened :('))
    print()

    printer.header('Using ColorPrinter to print strings:')
    printer(RED, 'red', GREEN, 'green', BLUE, 'blue')
    printer.info('Some info')
    printer.warning('I don\'t know about that...')
    printer.success('Achievement unlocked :)')
    printer.error('Something bad happened :(')
    print()

    print('Printing to a non-TTY:')
    original_isatty = sys.stdout.isatty
    sys.stdout.isatty = lambda: False
    printer.error('Something bad happened (not colorized)')
    sys.stdout.isatty = original_isatty
