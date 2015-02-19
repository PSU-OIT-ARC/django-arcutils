from django.contrib.admin.util import NestedObjects
from django.utils.six import add_metaclass


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def will_be_deleted_with(obj):
    """
    Pass in any Django model object that you intend to delete.
    This will iterate over all the model classes that would be affected by the
    deletion, yielding a two-tuple: the model class, and a set of all the
    objects of that type that would be deleted.
    """
    collector = NestedObjects(using="default")
    collector.collect([obj])
    # the collector returns a list of all objects in the database that
    # would be deleted if `obj` were deleted.
    for cls, list_of_items_to_be_deleted in collector.data.items():
        # remove obj itself from the list
        if cls == obj.__class__:
            list_of_items_to_be_deleted = set(item for item in list_of_items_to_be_deleted if item.pk != obj.pk)
            if len(list_of_items_to_be_deleted) == 0:
                continue

        yield cls, list_of_items_to_be_deleted


class IterableChoiceEnum(type):

    def __init__(cls, name, bases, attrs):
        cls._choices_dict = dict(cls)

    def __iter__(cls):
        """Simply return the iterator of the _choices tuple"""
        return iter(cls._choices)

    def __getitem__(cls, choice):
        """Return choice description via item access.

        Example::

            >>> class MyEnum(ChoiceEnum):
            ...
            ...     A = 1
            ...     B = 2
            ...
            ...     _choices = (
            ...         (A, 'Alpha'),
            ...         (B, 'Beta'),
            ...     )
            ...
            >>> MyEnum[MyEnum.A]
            'Alpha'

        """
        return cls._choices_dict[choice]

    def get(cls, choice, default=None):
        try:
            return cls[choice]
        except KeyError:
            return default


@add_metaclass(IterableChoiceEnum)
class ChoiceEnum(object):
    """
    This creates an iterable *class* (as opposed to an iterable *instance* of a
    class). Subclasses must define a class variable called `_choices` which is a
    list of 2-tuples. Subclasses can be passed directly to a field as the
    `choice` kwarg.

    For example:

    class FooType(ChoiceEnum):
        A = 1
        B = 2

        _choices = (
            (A, "Alpha"),
            (B, "Beta"),
        )


    class SomeModel(models.Model):
        foo = models.ChoiceField(choices=FooType)
    """
    _choices = ()
    # http://stackoverflow.com/questions/5434401/python-is-it-possible-to-make-a-class-iterable-using-the-standard-syntax
