from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from arcutils.drf import TemplateHTMLContextDictRenderer
from arcutils.response import get_redirect_location

from .perms import can_masquerade, can_masquerade_as
from .settings import settings, get_session_key, get_redirect_field_name
from .util import get_masquerade_user, is_masquerading


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        exclude = ['password']

    display_name = serializers.CharField(source='get_full_name')


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
        redirect_field_name = get_redirect_field_name()
        default = settings.get('default_redirect_url', '/')
        return get_redirect_location(request, redirect_field_name, default)


class MasqueradeSelectView(BaseView):

    renderer_classes = [TemplateHTMLContextDictRenderer, JSONRenderer]
    template_name = 'masquerade/select.html'
    context_object_name = 'masquerade'

    def get(self, request):
        user = request.user
        if not can_masquerade(user):
            raise PermissionDenied('You are not allowed to masquerade as another user')
        user_model = get_user_model()
        q = user_model.objects.exclude(pk=user.pk).order_by('first_name', 'last_name', 'email')
        users = [u for u in q if can_masquerade_as(user, u)]
        return Response({
            'users': UserSerializer(users, many=True).data,
            'other_users_count': q.count(),  # excludes request.user
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
