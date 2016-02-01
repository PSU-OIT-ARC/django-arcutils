from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from arcutils.threadlocals import get_current_user


class AuditModel(models.Model):

    """Mixin that adds standard auditing fields to a model.

    .. note: This requires 'arcutils.threadlocals.ThreadLocalMiddleware'
             to be added to MIDDLEWARE_CLASSES.

    """

    class Meta:
        abstract = True

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)ss_created',
        default=get_current_user)
    _updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='%(app_label)s_%(class)ss_updated',
        default=get_current_user, name='updated_by')

    @property
    def updated_by(self):
        return self._updated_by

    @updated_by.setter
    def updated_by(self, user):
        self._updated_by = user
        self._updated_by_set_manually = True


@receiver(pre_save)
def set_updated_by(sender, instance, **kwargs):
    do_auto_update = (
        issubclass(sender, AuditModel) and
        instance.pk is not None and  # Only auto-set existing records; use default for new
        not getattr(instance, '_updated_by_set_manually', False)  # Skip if set explicitly
    )
    if do_auto_update:
        user = get_current_user()
        if user is not None:
            instance.updated_by = user
