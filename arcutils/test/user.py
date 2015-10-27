from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class CouldNotLogInError(Exception):

    pass


class UserMixin(object):

    def create_user(self, username='foo', password='hunter2', groups=None, **kwargs):
        user = get_user_model()(username=username, **kwargs)
        user.set_password(password)
        user.save()
        if groups is not None:
            for group in groups:
                g, created = Group.objects.get_or_create(name=group)
                user.groups.add(g)
        return user

    def login_user(self, username, password):
        logged_in = self.client.login(username=username, password=password)
        if not logged_in:
            raise CouldNotLogInError('{}:{}'.format(username, password))

    def create_user_and_login(self, username='foo', password='hunter2', groups=None, **user_kwargs):
        user = self.create_user(username, password, groups=groups, **user_kwargs)
        self.login_user(username, password)
        return user
