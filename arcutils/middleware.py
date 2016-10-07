from django.core.exceptions import MiddlewareNotUsed
from django.http.response import HttpResponse


class MiddlewareBase:

    """Base class for Django 1.10-style middleware.

    The basic flow of middleware processing is:

        - Do something *before* the view (or next middleware) is called;
          this could be, for example, setting an attribute on the
          request.
        - Get the response object. By default, the response comes from
          calling all the middleware in the chain and finally the view.
          Any middleware can return an alternative response by *not*
          calling the next middleware in the chain.
        - Do something *after* the view (or next middleware) is called;
          this could be, for example, un-setting a request attribute or
          doing some other cleanup.

    This class provides A) hooks to implement the before and after steps
    noted above and B) shims to make 1.10-style middleware compatible
    with Django 1.9 and below.

    It also provides a way to easily disable middleware by implementing
    the :meth:`enabled` method and making it return ``False`` when the
    middleware should be disabled.

    """

    def __init__(self, get_response=None):
        if not self.enabled():
            raise MiddlewareNotUsed
        self._get_response = get_response

    def enabled(self) -> bool:
        """Indicates whether the middleware is enabled.

        Implement this to return ``False`` when the middleware should be
        removed from the middleware chain.

        """
        return True

    # Django 1.10 middleware implementation.

    def __call__(self, request) -> HttpResponse:
        """Django 1.10 middleware implementation."""
        self.before_view(request)
        response = self.get_response(request)
        self.after_view(request, response)
        return response

    def before_view(self, request) -> None:
        """Called before the view is called.

        This method should *not* return anything; the return value value
        will be ignored.

        """

    def get_response(self, request, fallback_response=None) -> HttpResponse:
        """Get the response.

        Typically, this will just be the response returned by the view.
        If the response requires alteration or other special handling,
        override this method.

        Args:
            fallback_response: This is used only on Django 1.9 and below
                where there's no ``get_response`` function and the
                response comes from :meth:`process_response`.

        """
        if self._get_response is None:
            # Django 1.9
            response = fallback_response
        else:
            # Django 1.10
            response = self._get_response(request)
        return response

    def after_view(self, request, response) -> None:
        """Called after the view is called.

        This method should *not* return anything; the return value value
        will be ignored.

        """

    # Shims for Django 1.9 and below.

    def process_request(self, request) -> None:
        self.before_view(request)

    def process_response(self, request, response) -> HttpResponse:
        self.after_view(request, response)
        response = self.get_response(request, fallback_response=response)
        return response
