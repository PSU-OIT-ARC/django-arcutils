from rest_framework.authentication import SessionAuthentication as BaseSessionAuthentication


class SessionAuthentication(BaseSessionAuthentication):

    """Make DRF return a 401 response for unauthenticated requests.

    By default, DRF returns a 403 for unauthenticated requests that
    require authorization. The problem with that is that it also returns
    a 403 when a user doesn't have permission to access a view--there's
    no easy way to distinguish between "403: you're not logged in" vs
    "403: you can't do that".

    """

    def authenticate_header(self, request):
        """Make DRF return a 401 response for unauthenticated requests.

        This returns a value for non-authenticated requests, which
        causes DRF return a 401 response. The actual value doesn't
        matter. Requests that require authentication will include the
        following header::

            WWW-Authenticate: Session

        """
        return 'Session'
