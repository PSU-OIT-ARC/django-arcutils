"""CAS.

    cas.middleware.CASMiddleware

"""
import logging
from operator import setitem
from xml.etree import ElementTree

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import FieldDoesNotExist

from arcutils.types.option import Some, Null


log = logging.getLogger(__name__)


# Map user object field names to CAS XML field names; these are
# attributes we'll try to extract from the CAS response in
# response_callback().
CAS_ATTR_MAP = (
    ('display_name', 'cas:DISPLAY_NAME'),
    ('first_name', 'cas:GIVEN_NAME'),
    ('last_name', 'cas:SN'),
    ('email', 'cas:MAIL'),
)

CAS_NS_MAP = {
    'cas': 'http://www.yale.edu/tp/cas',
}


def default_response_callback(tree):
    """If user does not exist, create from CAS response.

    This is called by the CAS auth back end if authentication is
    successful. If the corresponding user already exists, it will be
    returned as is; if it doesn't, a new user record will be created
    and returned.

    This attempts to populate some user attributes from the CAS
    response: ``first_name``, ``last_name``, and ``email``. If any of
    those attributes aren't found in the CAS response, they won't be
    set on the new user object; an error isn't raised because those
    attributes aren't critical and can be set later.

    The user's password is set to something unusable in the app's user
    table--i.e., we don't store passwords for CAS users in the app.

    ``tree`` is an :class:`xml.etree.elementtree.Element` created from
    the XML response returned from the PSU CAS system. Its structure
    looks like this::

        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationSuccess>
                <cas:user>wbaldwin</cas:user>
                <cas:attributes>
                      <cas:GIVEN_NAME>Wyatt</cas:GIVEN_NAME>
                      <cas:SN>Baldwin</cas:SN>
                      <cas:MAIL>wyatt.baldwin@pdx.edu</cas:MAIL>
                      <!-- Other fields elided -->
                </cas:attributes>
            </cas:authenticationSuccess>
        </cas:serviceResponse>

    """
    log.debug(ElementTree.tostring(tree).decode('utf-8'))
    cas_data = parse_cas_tree(tree)
    return get_or_create_user(cas_data)


def get_or_create_user(data):
    """Get user or create from CAS data.

    ``data`` must contain a 'username' key. It may also contain other
    user attributes, which will be set when creating a user (attributes
    that don't correspond to fields on the user model will be ignored).

    """
    user_model = get_user_model()
    username = data['username']

    try:
        user = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        pass
    else:
        return user

    # These defaults may be overridden by ``data``.
    user_args = {
        'email': '{username}@pdx.edu'.format(username=username),
    }

    for name, value in data.items():
        try:
            user_model._meta.get_field(name)
        except FieldDoesNotExist:
            pass
        else:
            user_args[name] = value

    is_superuser = username in getattr(settings, 'SUPERUSERS', ())
    is_staff = username in getattr(settings, 'STAFF', ())
    is_staff = is_staff or is_superuser

    user_args.update({
        'password': make_password(None),
        'is_staff': is_staff,
        'is_superuser': is_superuser,
    })

    user = user_model.objects.create(**user_args)
    return user


def parse_cas_tree(tree):
    """Pull data out of ElementTree ```tree`` into a dict.

    This maps the CAS attributes to normalized names using
    :const:`CAS_ATTR_MAP`.

    The dict will also include a ``username`` entry.

    """
    success = tree.find('cas:authenticationSuccess', CAS_NS_MAP)
    username = success.find('cas:user', CAS_NS_MAP).text.strip()
    attributes = success.find('cas:attributes', CAS_NS_MAP)
    cas_data = {}
    for name, cas_name in CAS_ATTR_MAP:
        with _get_cas_attr(attributes, cas_name) as option:
            option(some=lambda v: setitem(cas_data, name, v))
    cas_data['username'] = username
    return cas_data


def _get_cas_attr(attributes, cas_name, default=Null):
    value = attributes.find(cas_name, CAS_NS_MAP)
    if value is None:
        return Some(default) if default is not Null else Some(default)
    value = value.text.strip()
    return Some(value) if value else Null
