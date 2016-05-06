from enum import Enum


def dictfetchall(cursor):
    """Return all rows from cursor as a list of dicts."""
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def will_be_deleted_with(instance):
    """Get items that would be deleted along with model ``instance``.

    Pass in any Django model instance that you intend to delete and get
    an iterator of related objects that would also be deleted.

    Since this is implemented as a generator, if you want a list of
    items, you'll need to do ``list(will_be_deleted_with(instance))``.

    Args:
        instance: A Django ORM instance

    Returns:
        pairs: (model class, items of that class that will be deleted)

    """
    # XXX: Not sure why this import can't be moved to module scope.
    from django.contrib.admin.utils import NestedObjects
    # The collector returns a list of all objects in the database that
    # would be deleted if `obj` were deleted.
    collector = NestedObjects(using='default')
    collector.collect([instance])
    for cls, items_to_delete in collector.data.items():
        # XXX: Not sure the collector will ever include the original
        # XXX: instance, but this check was in the original version and
        # XXX: I don't have time to verify at the moment.
        if instance in items_to_delete:
            items_to_delete.remove(instance)
        if items_to_delete:
            yield cls, items_to_delete


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
