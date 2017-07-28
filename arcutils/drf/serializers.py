from django.utils import timezone

from rest_framework import serializers


class LocalDateTimeField(serializers.DateTimeField):

    """Converts datetime to local time before serialization."""

    def to_representation(self, value):
        value = timezone.localtime(value)
        return super().to_representation(value)
