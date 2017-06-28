from django import template

from .. import perms
from ..settings import get_user_attr, is_enabled


register = template.Library()


@register.filter
def is_masquerading(user):
    if not is_enabled():
        return False
    info = getattr(user, get_user_attr(), None)
    return info['is_masquerading']


@register.filter
def can_masquerade(user):
    return perms.can_masquerade(user)


@register.filter
def can_masquerade_as(user, masquerade_user):
    return perms.can_masquerade_as(user, masquerade_user)
