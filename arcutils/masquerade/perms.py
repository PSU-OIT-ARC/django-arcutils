from .settings import is_enabled, settings


def can_masquerade(user):
    if not is_enabled():
        return False
    func = settings.get('can_masquerade')
    if func:
        return func(user)
    return user.is_staff or user.is_superuser


def can_masquerade_as(user, masquerade_user):
    if not can_masquerade(user):
        return False
    func = settings.get('can_masquerade_as')
    if func:
        return func(user)
    return not (masquerade_user.is_superuser or masquerade_user == user)
