from ..middleware import MiddlewareBase
from .perms import can_masquerade
from .settings import get_user_attr, is_enabled
from .util import get_masquerade_user, is_masquerading


class MasqueradeMiddleware(MiddlewareBase):

    def enabled(self):
        return is_enabled()

    def before_view(self, request):
        masquerade_info = {}
        actual_user = request.user
        if is_masquerading(request):
            request.user = get_masquerade_user(request, source='session')
            masquerade_info.update({
                'actual_user': actual_user,
                'can_masquerade': True,
                'is_masquerading': True,
            })
        else:
            masquerade_info.update({
                'can_masquerade': can_masquerade(actual_user),
                'is_masquerading': False,
            })
        setattr(request.user, get_user_attr(), masquerade_info)
