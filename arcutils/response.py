from urllib.parse import urlparse, urlunparse

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.http import is_safe_url


def get_redirect_location(request, redirect_field_name=REDIRECT_FIELD_NAME, default='/'):
    """Attempt to choose an optimal redirect location.

    If a location is specified via a request parameter, that location
    will be used.

    If a location is specified via POST or PUT data, that location will
    be used.

    In either of the above two cases, the name of the parameter and data
    field is specified by ``redirect_field_name``, which defaults to
    "next".

    Otherwise, the preferred option is to redirect back to the referring
    page.

    If there's no referrer, the default is used.

    In any case, the redirect location must be safe (same host, safe
    scheme). Otherwise, the ``default`` location will be used. If the
    default location isn't safe, "/" will be used as a last resort.

    """
    host = request.get_host()
    location = request.GET.get(redirect_field_name) or request.POST.get(redirect_field_name)

    if location:
        from_referrer = False
    else:
        location = request.META.get('HTTP_REFERER')
        from_referrer = bool(location)

    if not is_safe_url(location, host):
        default = default or '/'
        if not is_safe_url(default, host):
            default = '/'
        location = default
    elif from_referrer:
        info = urlparse(location)
        if info.netloc == host:
            # Clear scheme and host (AKA netloc) to get just the path of
            # the referrer. Also, ensure the path is set for consistency.
            new_info = ('', '', info.path or '/') + info[3:]
            location = urlunparse(new_info)

    return location
