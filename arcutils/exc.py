import warnings


class ARCUtilsDeprecationWarning(DeprecationWarning):

    @classmethod
    def warn(cls, message, stacklevel=2):
        warnings.warn(message, cls, stacklevel)


warnings.simplefilter('default', ARCUtilsDeprecationWarning)
