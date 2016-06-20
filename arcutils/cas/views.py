import logging

from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.contrib import auth

from .settings import settings
from .utils import login_url, logout_url, redirect_url, service_url


log = logging.getLogger(__name__)


SESSION_KEY_REDIRECT_TO = 'CAS.redirect_to'


def login(request, redirect_to=None):
    user = request.user

    if not redirect_to:
        # This pulls the redirect location out of the request parameters
        # if available. Falls back to CAS.redirect_url if set or /.
        redirect_to = redirect_url(request)

    if user and user.is_authenticated():
        log.debug('User {user.username} already authenticated'.format(user=user))
        return HttpResponseRedirect(redirect_to)

    # Not authenticated; go to CAS and login. CAS will redirect back to
    # the service URL with a ticket to be validated. The service URL is
    # passed to CAS via the service query parameter of the login URL.
    url = login_url(request)
    session_key = settings.get('session_key.redirect_to', SESSION_KEY_REDIRECT_TO)
    request.session[session_key] = redirect_to
    log.debug('Redirecting to CAS for login: {url}'.format(url=url))
    return HttpResponseRedirect(url)


def validate(request):
    # At this point, the user has authenticated with CAS. CAS has
    # redirected back here with a ticket parameter tacked onto the URL.
    # Here, we validate the ticket then do the usual Django login
    # procedure.
    ticket = request.GET['ticket']
    service = service_url(request)
    user = auth.authenticate(ticket=ticket, service=service)
    if user is not None:
        # Allow users to be deactivated locally regardless of CAS
        # account status.
        if user.is_active:
            auth.login(request, user)
            session_key = settings.get('session_key.redirect_to', SESSION_KEY_REDIRECT_TO)
            redirect_to = request.session.pop(session_key, None) or '/'
            return HttpResponseRedirect(redirect_to)
        else:
            raise PermissionDenied('Your account has been deactivated locally.')
    else:
        raise PermissionDenied(
            'Unable to log in at this time; please try again later (CAS validation failed).')


def logout(request):
    # Local logout; does *not* do CAS logout
    auth.logout(request)
    if settings.get('logout_completely', True):
        # CAS logout
        return HttpResponseRedirect(logout_url(request))
    else:
        return HttpResponseRedirect(redirect_url(request))
