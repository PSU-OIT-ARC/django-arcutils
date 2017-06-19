import logging

from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.template import loader
from django.views.decorators.csrf import requires_csrf_token


log = logging.getLogger(__name__)


@requires_csrf_token
def bad_request(request, exception=None, template_name='400.html'):
    """Override default Django bad_request view so context is passed.

    Otherwise, static files won't be loaded and default context vars
    won't be available (&c).

    If loading or rendering the template causes an error, a bare 400
    response will be returned.

    To use this in a project, import it into the project's root
    urls.py and add a 400.html template.

    .. note:: The ``exception`` arg was added in Django 1.9.

    """
    try:
        template = loader.get_template(template_name)
        body, content_type = template.render({'request': request}, request), None
    except Exception:
        log.exception('Exception encountered while rendering 400 error')
        body, content_type = '<h1>Bad Request (400)</h1>', 'text/html'
    return HttpResponseBadRequest(body, content_type=content_type)


@requires_csrf_token
def server_error(request, template_name='500.html'):
    """Override default Django server_error view so context is passed.

    Otherwise, static files won't be loaded and default context vars
    won't be available (&c).

    If loading or rendering the template causes an error, a bare 500
    response will be returned.

    """
    try:
        template = loader.get_template(template_name)
        body, content_type = template.render({'request': request}, request), None
    except Exception:
        log.exception('Exception encountered while rendering 500 error')
        body, content_type = '<h1>Server Error (500)</h1>', 'text/html'
    return HttpResponseServerError(body, content_type=content_type)
