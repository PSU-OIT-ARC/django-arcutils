from django.contrib.auth import get_user_model

from rest_framework.exceptions import ParseError, PermissionDenied

from .perms import can_masquerade, can_masquerade_as
from .settings import get_param_name, get_session_key


def get_masquerade_user(request, source, masquerade_user_id=None):
    """Get masquerade user from ``source``.

    If ``masquerade_user_id`` isn't set, ``source`` must be one of
    "data" (i.e., POST data) or "session".

    Ensures ``request.user`` is allowed to masquerade (at all) and is
    allowed to masquerade as the specified user.

    """
    if not can_masquerade(request.user):
        raise PermissionDenied('You are not allowed to masquerade as another user')

    if masquerade_user_id is None:
        if source == 'data':
            key = get_param_name()
            try:
                masquerade_user_id = request.data[key]
            except KeyError:
                raise ParseError('Missing {key} POST parameter'.format(key=key))
        elif source == 'session':
            key = get_session_key()
            try:
                masquerade_user_id = request.session[key]
            except KeyError:
                raise ParseError('Missing {key} session key'.format(key=key))

    user_model = get_user_model()
    try:
        masquerade_user = user_model.objects.get(pk=masquerade_user_id)
    except user_model.DoesNotExist:
        raise ParseError('Masquerade user does not exist')

    if not can_masquerade_as(request.user, masquerade_user):
        raise PermissionDenied('You are not allowed to masquerade as that user')

    return masquerade_user


def is_masquerading(request):
    """Indicates whether the current (actual) user is masquerading."""
    return get_session_key() in request.session
