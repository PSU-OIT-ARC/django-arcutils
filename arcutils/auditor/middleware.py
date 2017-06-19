import uuid
from collections import namedtuple

from arcutils.middleware import MiddlewareBase

from django.utils import timezone

from .utils import Sequencer


AuditorInfo = namedtuple('AuditorInfo', 'user timestamp changeset_id sequencer')


class AuditorMiddleware(MiddlewareBase):

    def before_view(self, request):
        info = AuditorInfo(request.user, timezone.now(), uuid.uuid4(), Sequencer())
        request.auditor_info = info

    def after_view(self, request, response):
        del request.auditor_info
