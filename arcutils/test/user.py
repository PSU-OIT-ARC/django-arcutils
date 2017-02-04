from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from arcutils.decorators import cached_property


class CouldNotLogInError(Exception):

    pass


class UserMixin:

    @cached_property
    def user_model(self):
        return get_user_model()

    @cached_property('user_model')
    def username_field(self):
        return self.user_model.USERNAME_FIELD

    def create_user(self, username='foo', password='hunter2', groups=(), **kwargs):
        kwargs[self.username_field] = username
        user = self.user_model(**kwargs)
        user.set_password(password)
        user.save()

        for group in groups:
            if isinstance(group, str):
                group = self.create_group(group)
            elif not isinstance(group, Group):
                raise TypeError(
                    'Expected a group name or a Group instance; got a {0.__class__}'.format(group))
            user.groups.add(group)

        return user

    def login_user(self, username, password):
        logged_in = self.client.login(username=username, password=password)
        if not logged_in:
            raise CouldNotLogInError('{}:{}'.format(username, password))

    def create_user_and_login(self, username='foo', password='hunter2', groups=(), **kwargs):
        user = self.create_user(username, password, groups=groups, **kwargs)
        self.login_user(username, password)
        return user

    def create_group(self, name):
        group, _ = Group.objects.get_or_create(name=name)
        return group
