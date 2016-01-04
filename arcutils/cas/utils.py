import posixpath
from operator import setitem
from urllib.parse import urlencode, urljoin

from arcutils.response import REDIRECT_FIELD_NAME, get_redirect_location
from arcutils.settings import get_setting
from arcutils.types.option import Some, Null


CAS_NS_MAP = {
    'cas': 'http://www.yale.edu/tp/cas',
}


# Map user object field names to CAS XML field names; these are
# attributes we'll try to extract from the CAS response in
# response_callback().
CAS_ATTR_MAP = (
    ('username', 'cas:UID'),
    ('display_name', 'cas:DISPLAY_NAME'),
    ('first_name', 'cas:GIVEN_NAME'),
    ('last_name', 'cas:SN'),
    ('email', 'cas:MAIL'),
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
                <cas:user>wbaldwin</cas:user>
                <cas:attributes>
                    <cas:UID>wbaldwin</cas:UID>
                    <cas:DISPLAY_NAME>Wyatt Baldwin</cas:DISPLAY_NAME>
                    <cas:GIVEN_NAME>Wyatt</cas:GIVEN_NAME>
                    <cas:SN>Baldwin</cas:SN>
                    <cas:MAIL>wbaldwin@pdx.edu</cas:MAIL>
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


def login_url(request, next=None):
    # Include next location as a parameter in the service URL sent to
    # CAS so that when CAS redirects back to the app after login, we
    # know where to send the user.
    params = request.GET.copy()
    params[REDIRECT_FIELD_NAME] = next or redirect_url(request)
    service_path = '?'.join((request.path, params.urlencode()))
    service_url = request.build_absolute_uri(service_path)

    path = get_setting('CAS.login_path', 'login')
    params = {'service': service_url}
    return make_cas_url(path, **params)


def logout_url(request, next=None):
    path = get_setting('CAS.logout_path', 'logout')
    params = {}
    if next is not None:
        next = request.build_absolute_uri(next)
        params = {'url': next}
    return make_cas_url(path, **params)


def make_cas_url(*path, **params):
    base_url = get_setting('CAS.base_url')
    path = posixpath.join(*path)
    url = urljoin(base_url, path)
    if params:
        params = urlencode(params)
        url = '?'.join((url, params))
    return url


def redirect_url(request):
    default = get_setting('CAS.redirect_url', default=None)
    url = get_redirect_location(request, default=default)
    return url
