from django.contrib.auth import get_user_model
from django.utils.http import is_safe_url

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from arcutils.renderers import TemplateHTMLContextDictRenderer

from .perms import can_masquerade, can_masquerade_as
from .settings import get_setting, get_session_key, get_redirect_field_name
from .util import get_masquerade_user, is_masquerading


class BaseView(APIView):

    permission_classes = [IsAuthenticated]

    def set_masquerade_user(self, request, masquerade_user):
        request.session[get_session_key()] = masquerade_user.pk

    def unset_masquerade_user(self, request):
        if is_masquerading(request):
            del request.session[get_session_key()]

    def redirect(self, request):
        location = self.get_redirect_location(request)
        return Response(status=status.HTTP_303_SEE_OTHER, headers={'location': location})

    def get_redirect_location(self, request):
        field_name = get_redirect_field_name()
        location = request.query_params.get(field_name)
        if not location:
            location = request.data.get(field_name)
        if not location:
            location = request.META.get('HTTP_REFERER')
        if not is_safe_url(location):
            location = None
        if not location:
            location = get_setting('default_redirect_url', '/')
        return location


class MasqueradeSelectView(BaseView):

    renderer_classes = [TemplateHTMLContextDictRenderer]
    template_name = 'masquerade/select.html'
    context_object_name = 'masquerade'

    def get(self, request):
        if not can_masquerade(request.user):
            raise PermissionDenied('You are not allowed to masquerade as another user')
        user_model = get_user_model()
        users = user_model.objects.all().order_by('first_name', 'last_name', 'email')
        users = [u for u in users if can_masquerade_as(request.user, u)]
        return Response({
            'users': users,
            get_redirect_field_name(): self.get_redirect_location(request),
        })


class MasqueradeView(BaseView):

    def post(self, request):
        masquerade_user = get_masquerade_user(request, source='data')
        self.set_masquerade_user(request, masquerade_user)
        return self.redirect(request)


class UnmasqueradeView(BaseView):

    def post(self, request):
        self.unset_masquerade_user(request)
        return self.redirect(request)
