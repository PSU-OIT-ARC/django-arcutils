import posixpath
from operator import setitem
from urllib.parse import urlencode, urljoin

from django.core.urlresolvers import reverse

from arcutils.response import get_redirect_location
from arcutils.types.option import Some, Null

from .settings import settings


CAS_NS_MAP = {
    'cas': 'http://www.yale.edu/tp/cas',
}


# Map user object field names to CAS XML attribute names. The CAS
# attributes are extracted from the CAS XML response and passed to
# response callbacks.
CAS_ATTR_MAP = (
    ('username', 'cas:uid'),
    ('display_name', 'cas:display_name'),
    ('first_name', 'cas:given_name'),
    ('last_name', 'cas:sn'),
    ('email', 'cas:mail'),
)


def get_cas_attr(attributes, cas_name, default=Null):
    value = tree_find(attributes, cas_name)
    if value is None:
        return Some(default) if default is not Null else Some(default)
    value = value.text.strip()
    return Some(value) if value else Null


def tree_find(tree, name):
    return tree.find(name, CAS_NS_MAP)


def parse_cas_tree(tree):
    """Pull data out of ElementTree ```tree`` into a dict.

    This maps the CAS attributes to normalized names using
    :const:`CAS_ATTR_MAP`.

    ``tree`` is an :class:`xml.etree.elementtree.Element` created from
    the XML response returned from the PSU CAS system. Its structure
    looks like this::

        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationSuccess>
                <cas:user>bobs</cas:user>
                <cas:attributes>
                    <cas:uid>bobs</cas:uid>
                    <cas:display_name>Bob Smith</cas:display_name>
                    <cas:given_name>Bob</cas:given_name>
                    <cas:sn>Smith</cas:sn>
                    <cas:mail>bobs@pdx.edu</cas:mail>
                </cas:attributes>
            </cas:authenticationSuccess>
        </cas:serviceResponse>

    """
    success = tree_find(tree, 'cas:authenticationSuccess')
    attributes = tree_find(success, 'cas:attributes')
    cas_data = {}
    for name, cas_name in CAS_ATTR_MAP:
        with get_cas_attr(attributes, cas_name) as option:
            option(some=lambda v: setitem(cas_data, name, v))
    return cas_data


def login_url(request):
    """Return CAS login URL with service parameter.

    Something like this::

        https://cas.host.example.com/login?service={service_url()}

    """
    path = settings.get('login_path', 'login')
    params = {'service': service_url(request)}
    return make_cas_url(path, **params)


def logout_url(request):
    """Return CAS logout URL.

    Something like this::

        https://cas.host.example.com/logout

    """
    path = settings.get('logout_path', 'logout')
    return make_cas_url(path)


def make_cas_url(*path, **params):
    """Tack ``path`` segments and query ``params`` onto base CAS URL.

    If ``path`` starts with a slash or contains a segment that does, the
    path prefix of the base CAS URL will be overwritten.

    """
    base_url = settings.get('base_url')
    path = posixpath.join(*path)
    url = urljoin(base_url, path)
    if params:
        params = urlencode(params)
        url = '?'.join((url, params))
    return url


def redirect_url(request):
    """Return CAS redirect URL.

    This is used to figure out where to send the user after login or
    logout.

    If the ``CAS.redirect_url`` setting is set, that will be used;
    otherwise, fall back to ``next`` parameter, referrer, or /.

    """
    default = settings.get('redirect_url', default=None)
    url = get_redirect_location(request, default=default)
    return url


def service_url(request):
    """Return service URL/ID.

    The service URL is both a unique identifier *and* where CAS
    redirects to after successful login.

    In this context, "service" refers to the application that is using
    CAS for login.

    """
    path = reverse('cas-validate')
    url = request.build_absolute_uri(path)
    return url
