import uuid

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):

    class Meta:
        ordering = ['timestamp', 'changeset_id', 'sequence']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    timestamp = models.DateTimeField()
    changeset_id = models.UUIDField()
    sequence = models.PositiveIntegerField()
    message = models.CharField(max_length=255)

    content_type = models.ForeignKey(ContentType)
    object_id = models.CharField(max_length=255)
    object = GenericForeignKey('content_type', 'object_id')

    created = models.BooleanField()
    deleted = models.BooleanField()

    field_name = models.CharField(max_length=255)
    old_value = JSONField(null=True, blank=True)
    new_value = JSONField(null=True, blank=True)

    @property
    def type(self):
        if self.created:
            return 'creation'
        if self.deleted:
            return 'deletion'
        return 'update'

    def __str__(self):
        temp = (
            '{self.content_type.name}({self.object_id}).{self.field_name}: '
            '{self.old_value} => {self.new_value}')
        temp = temp.format_map(locals())
        return temp
