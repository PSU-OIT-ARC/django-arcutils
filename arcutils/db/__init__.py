from enum import Enum


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
    from django.contrib.admin.util import NestedObjects
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


class ChoiceEnum(Enum):

    """An enum type for use w/ the ``choices`` arg of model fields.

    This is based on the built-in Enum type in Python 3.4+. For Python
    3.3, a back-ported version will be installed.

    Example usage::

        class LayoutType(ChoiceEnum):

            text_only = 0
            chart = 1
            map = 2
            image = 3


        class Page(models.Model):

            layout = models.IntegerField(
                choices=LayoutType.as_choices(), default=LayoutType.text_only.value)

    You can instead use text values if that's more appropriate::

        class Status(ChoiceEnum):

            new = 'new'
            open = 'open'
            resolved = 'resolved'

        class Ticket(models.Model):

            status = models.CharField(
                max_length=255, choices=Status.as_choices(), default=Status.new.value)

    """

    @classmethod
    def as_choices(cls, as_dict=False):
        """Return list of (value, label) pairs for use with ``choices``.

        If ``as_dict`` is specified, a list of dictionaries with 'value'
        and 'label' keys will be returned instead of a list of tuples.

        Using the ``LayoutType`` example from the class docstring::

            >>> LayoutType.as_choices()
            [(0, 'Text only'), (1, 'Chart'), (2, 'Map'), (3, 'Image')]

        """
        choices = [(choice.value, choice.label) for choice in cls]
        if as_dict:
            choices = [{'value': value, 'label': label} for (value, label) in choices]
        return choices

    @property
    def label(self):
        """Get the label for a choice.

        Using the ``LayoutType`` example from the class docstring::

            >>> LayoutType['image'].label
            'Image'
            >>> LayoutType.image.label
            'Image'
            >>> LayoutType(LayoutType.image).label
            'Image'

        """
        parts = self.name.split('_')
        parts[0] = parts[0].title()
        return ' '.join(parts)

    def __str__(self):
        return self.label
