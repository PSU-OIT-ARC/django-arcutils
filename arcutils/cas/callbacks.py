"""CAS.

    cas.middleware.CASMiddleware

"""
import logging
from xml.etree import ElementTree

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import FieldDoesNotExist


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

    user_model = get_user_model()

    success = tree.find('cas:authenticationSuccess', CAS_NS_MAP)
    username = success.find('cas:user', CAS_NS_MAP).text.strip()
    attributes = success.find('cas:attributes', CAS_NS_MAP)

    def get_attribute(cas_name, default=None):
        value = attributes.find(cas_name, CAS_NS_MAP)
        return default if value is None else value.text.strip()

    try:
        user = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        pass
    else:
        return user

    is_superuser = username in getattr(settings, 'SUPERUSERS', ())
    is_staff = username in getattr(settings, 'STAFF', ())
    is_staff = is_staff or is_superuser

    user_args = {
        'username': username,
        'password': make_password(None),
        'is_staff': is_staff,
        'is_superuser': is_superuser,
        # This default email address will be overridden if there's an
        # email address in the CAS attributes.
        'email': '{username}@pdx.edu'.format(username=username)
    }

    for name, cas_name in CAS_ATTR_MAP:
        try:
            user_model._meta.get_field(name)
        except FieldDoesNotExist:
            pass
        else:
            value = get_attribute(cas_name)
            if value is not None:
                user_args[name] = value

    user = user_model.objects.create(**user_args)
    return user
