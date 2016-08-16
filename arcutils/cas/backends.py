import logging
import textwrap
from xml.etree import ElementTree
from urllib.request import urlopen

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import make_password
from django.utils.module_loading import import_string

from arcutils.exc import ARCUtilsDeprecationWarning
from arcutils.decorators import cached_property

from .settings import settings
from .utils import make_cas_url, parse_cas_tree, tree_find


log = logging.getLogger(__name__)


class CASBackend:

    """CAS authentication backend."""

    def authenticate(self, ticket, service):
        cas_data = self._validate_ticket(ticket, service)

        if self._response_callbacks:
            ARCUtilsDeprecationWarning.warn(
                'The use of CAS response callbacks is deprecated. Subclass CASBackend or'
                'CASModelBackend and override the get_or_create_user() method instead.')
            log.debug('Calling CAS response callbacks...')
            for callback in self._response_callbacks:
                callback(cas_data)

        return self.get_or_create_user(cas_data) if cas_data else None

    def get_or_create_user(self, cas_data, **overrides):
        """Get user.

        ``cas_data`` must contain a 'username' key. If the corresponding
        user already exists, it will be returned as is; if it doesn't, a
        new user record will be created and returned.

        .. note:: The ``CAS.auto_create_user`` setting can be set to
                  ``False`` to disable the auto-creation of users.

        ``overrides`` are passed through to :meth:`create_user`.

        """
        user_model = get_user_model()
        username = cas_data['username']
        try:
            return user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            pass
        if settings.get('auto_create_user'):
            return self.create_user(cas_data, **overrides)

    def create_user(self, cas_data, **overrides):
        """Create user from CAS data.

        This attempts to populate some user attributes from the CAS
        response: ``first_name``, ``last_name``, and ``email``. Any of
        those attributes that aren't found in the CAS response will be
        set to a default value on the new user object.

        The user's password is set to something unusable in the app's user
        table--i.e., we don't store passwords for CAS users in the app.

        If the ``STAFF`` setting is set, the user's ``is_staff`` flag
        will be set according to whether their username is in the
        ``STAFF`` list.

        If the ``SUPERUSER`` setting is set, the user's ``is_staff``
        and ``is_superuser`` flags will be set according to whether
        their username is in the ``SUPERUSERS`` list.

        ``overrides`` can be passed to override the values of *any* of
        the fields mentioned above or to set additional fields. This is
        useful in subclasses to avoid re-saving the user.

        .. note:: This method assumes a standard user model. It may not
                  or may not work with custom user models.

        """
        user_model = get_user_model()
        username = cas_data['username']

        user_args = {
            'email': '{username}@pdx.edu'.format(username=username),
            'first_name': '',
            'last_name': '',
        }

        for name, value in user_args.items():
            if name in cas_data:
                user_args[name] = cas_data[name]

        staff = getattr(django_settings, 'STAFF', None)
        superusers = getattr(django_settings, 'SUPERUSERS', None)
        is_staff = bool(staff and username in staff)
        is_superuser = bool(superusers and username in superusers)

        user_args.update({
            'username': username,
            'password': make_password(None),
            'is_staff': is_staff or is_superuser,
            'is_superuser': is_superuser,
        })

        user_args.update(overrides)

        return user_model.objects.create(**user_args)

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model._default_manager.get(pk=user_id)
        except user_model.DoesNotExist:
            return None

    def _validate_ticket(self, ticket, service):
        path = settings.get('validate_path')
        params = {'ticket': ticket, 'service': service}
        url = make_cas_url(path, **params)

        log.debug('Validating CAS ticket: {url}'.format(url=url))

        with urlopen(url) as fp:
            response = fp.read()

        tree = ElementTree.fromstring(response)
        log.debug('CAS response:\n%s', ElementTree.tostring(tree, encoding='unicode'))

        if tree is None:
            raise ValueError('Unexpected CAS response:\n{response}'.format(response=response))
        success = tree_find(tree, 'cas:authenticationSuccess')

        if success:
            log.debug('CAS ticket validated: {url}'.format(url=url))
            return parse_cas_tree(tree)
        else:
            message = 'CAS ticket not validated: {url}\n{detail}'
            failure = tree_find(tree, 'cas:authenticationFailure')
            if failure:
                detail = failure.text.strip()
            else:
                detail = ElementTree.tostring(tree, encoding='unicode').strip()
            detail = textwrap.indent(detail, ' ' * 4)
            log.error(message.format(url=url, detail=detail))
            return None  # Explicit

    @cached_property
    def _response_callbacks(self):
        callbacks = settings.get('response_callbacks', [])
        for i, cb in enumerate(callbacks):
            if isinstance(cb, str):
                callbacks[i] = import_string(cb)
        return callbacks


class CASModelBackend(CASBackend, ModelBackend):

    """CAS/Model authentication backend.

    Use CASBackend's authenticate() method while also getting all the
    default permissions handling from ModelBackend.

    """
