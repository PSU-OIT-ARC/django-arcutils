import logging
import textwrap
from xml.etree import ElementTree
from urllib.request import urlopen

from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

from django.contrib.auth.backends import ModelBackend

from arcutils.decorators import cached_property
from arcutils.settings import get_setting

from .utils import make_cas_url, parse_cas_tree, tree_find


log = logging.getLogger(__name__)


class CASBackend:

    """CAS authentication backend."""

    def authenticate(self, ticket, service):
        username = self._verify_ticket(ticket, service)
        if username:
            user_model = get_user_model()
            try:
                user = user_model.objects.get(username=username)
            except user_model.DoesNotExist:
                if get_setting('CAS.auto_create_user', True):
                    user = user_model.objects.create_user(username, None)
                    user.save()
                else:
                    user = None
        else:
            user = None
        return user

    def _verify_ticket(self, ticket, service, suffix=None):
        path = get_setting('CAS.verify_path')
        params = {'ticket': ticket, 'service': service}
        url = make_cas_url(path, **params)

        log.debug('Verifying CAS ticket: {url}'.format(url=url))

        with urlopen(url) as fp:
            response = fp.read()

        tree = ElementTree.fromstring(response)
        log.debug(ElementTree.tostring(tree, encoding='unicode'))

        if tree is None:
            raise ValueError('Unexpected CAS response:\n{response}'.format(response=response))
        success = tree_find(tree, 'cas:authenticationSuccess')

        if success:
            log.debug('CAS ticket verified: {url}'.format(url=url))
            log.debug('Calling CAS response callbacks...')
            cas_data = parse_cas_tree(tree)
            for callback in self._response_callbacks:
                callback(cas_data)
            return cas_data['username']
        else:
            message = 'CAS ticket not verified: {url}\n{detail}'
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
        callbacks = get_setting('CAS.response_callbacks')
        for i, cb in enumerate(callbacks):
            if isinstance(cb, str):
                callbacks[i] = import_string(cb)
        return callbacks


class CASModelBackend(CASBackend, ModelBackend):

    """CAS/Model authentication backend.

    Use CASBackend's authenticate() method while also getting all the
    default permissions handling from ModelBackend.

    """
