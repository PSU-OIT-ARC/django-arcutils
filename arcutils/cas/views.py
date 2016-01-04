import logging

from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.contrib import auth

from arcutils.settings import get_setting

from .utils import login_url, logout_url, redirect_url


log = logging.getLogger(__name__)


def login(request, next=None):
    user = request.user

    if not next:
        # This pulls the next location out of the request parameters if
        # available. Falls back to CAS.redirect_url if set or /.
        next = redirect_url(request)

    if user and user.is_authenticated():
        log.debug('User {user.username} already authenticated'.format(user=user))
        return HttpResponseRedirect(next)

    log.debug('User not authenticated; doing CAS auth')

    ticket = request.GET.get('ticket')

    if ticket is None:
        # Not authenticated with CAS; go to CAS and login. CAS will
        # redirect back here with a ticket.
        url = login_url(request, next)
        log.debug('No CAS ticket found; redirecting to CAS for login: {url}'.format(url=url))
        return HttpResponseRedirect(url)
    else:
        # Authenticated with CAS. Verify the ticket, then do the usual
        # Django login procedure.

        # CAS redirects back to the service URL it was passed via the
        # service query parameter. CAS tacks the ticket parameter onto
        # the service URL, which needs to be removed before verifying
        # the ticket.
        params = request.GET.copy()
        del params['ticket']
        location = '?'.join((request.path, params.urlencode()))
        service = request.build_absolute_uri(location)

        log.debug('CAS ticket found; authenticating service: {service}'.format(service=service))
        user = auth.authenticate(ticket=ticket, service=service)
        if user is not None:
            # Allow users to be deactivated locally regardless of CAS
            # account status.
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(next)
            else:
                raise PermissionDenied('Your account has been deactivated locally.')
        else:
            raise PermissionDenied(
                'Unable to log in at this time; please try again later (CAS verification failed).')

def logout(request, next=None):
    # Local logout; does *not* do CAS logout
    auth.logout(request)
    if next is None:
        next = redirect_url(request)
    if get_setting('CAS.logout_completely', True):
        # CAS logout
        return HttpResponseRedirect(logout_url(request, next))
    else:
        return HttpResponseRedirect(next)
