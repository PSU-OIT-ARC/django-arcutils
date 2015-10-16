"""CAS.

    cas.middleware.CASMiddleware

"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password


# Map user object field names to CAS XML field names; these are
# attributes we'll try to extract from the CAS response in
# response_callback().
CAS_ATTR_MAP = (
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
    user_model = get_user_model()
    success = get_success(tree)
    username = get_username(success)

    try:
        user = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        pass
    else:
        return user

    is_staff = username in getattr(settings, 'STAFF', ())
    is_superuser = username in getattr(settings, 'SUPERUSER', ())
    user_args = {
        'username': username,
        'password': make_password(None),
        'is_staff': is_staff or is_superuser,
        'is_superuser': is_superuser,
    }

    cas_attrs = get_attributes(success)

    def set_arg_from_cas_attr(name, cas_name, destination):
        value = cas_attrs.find(cas_name, CAS_NS_MAP)
        if value is not None:
            destination[name] = value.text.strip()

    for n, c in CAS_ATTR_MAP:
        set_arg_from_cas_attr(n, c, user_args)

    user = user_model.objects.create(**user_args)
    return user


def get_success(tree):
    return tree.find('cas:authenticationSuccess', CAS_NS_MAP)


def get_username(success):
    return success.find('cas:user', CAS_NS_MAP).text.strip()


def get_attributes(success):
    return success.find('cas:attributes', CAS_NS_MAP)
