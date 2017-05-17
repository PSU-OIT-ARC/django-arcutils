"""ARC-specific Django Admin enhancements.

This is used just like the built-in Django admin site:

- Add one of the following to ``INSTALLED_APPS``:
  - 'arcutils.admin.AdminConfig' if *not* using CAS auth
  - 'arcutils.admin.CASAdminConfig' if using CAS auth
  - 'django.contrib.admin.apps.SimpleAdminConfig' if you don't want
    admin modules to be auto-discovered
- Register modules to :global:`site` or :global:`cas_site`
- Ensure other requirements are met as listed in the Django admin site
  docs (add the appropriate middleware, context processors, etc)

Example::

    # Project settings
    INSTALLED_APPS = [
        'arcutils.admin.CASAdminConfig',  # Replaces 'django.contrib.admin'
        ...
    ]

    # Project root URLconf:
    from arcutils import admin
    urlpatterns = [
        ...
        url(r'^admin/', include(admin.cas_site.urls)),
    ]

    # Example admin module in project:
    from arcutils import admin  # Replaces `from django.contrib import admin`
    from .models import SomeModel
    admin.cas_site.register(SomeModel)

"""
from django.conf import settings
from django.contrib.admin import AdminSite as DefaultAdminSite, site as default_admin_site
from django.contrib.admin.apps import SimpleAdminConfig
from django.core.urlresolvers import reverse
from django.utils.module_loading import autodiscover_modules
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache

from .cas import views as cas_views
from .decorators import cached_property
from .response import get_redirect_location


class AdminConfig(SimpleAdminConfig):

    """Replacement for ``django.contrib.admin``.

    Auto-discovers admin modules and registers them to the default
    ARCUtils admin :global:`site` instance.

    This replaces ``django.contrib.admin`` in ``INSTALLED_APPS`` when
    using the default ARCUtils local settings.

    """

    def ready(self):
        super().ready()
        autodiscover(site)


class CASAdminConfig(SimpleAdminConfig):

    """Replacement for django.contrib.admin.

    Auto-discovers admin modules and registers them to the ARCUtils
    admin :global:`cas_site` instance.

    """

    def ready(self):
        super().ready()
        autodiscover(cas_site)


class AdminSite(DefaultAdminSite):

    """Admin site with some enhancements.

    Features:

    - Adds project title as link to admin site header
    - Allows superusers to access the admin site (even if they aren't
      staff)

    """

    @cached_property
    def site_header(self):
        urls = {'home': reverse('home'), 'admin': reverse('admin:index')}
        project_title = settings.PROJECT.title
        return mark_safe(
            '<a href="{urls[home]}" title="View {project_title} site">{project_title}</a> '
            '<a href="{urls[admin]}" title="Admin home">Administration</a>'
            .format(**locals())
        )

    def has_permission(self, request):
        if not request.user.is_active:
            return False
        if request.user.is_superuser:
            return True
        return super().has_permission(request)


class CASMixin:

    @never_cache
    def login(self, request, extra_context=None):
        redirect_to = get_redirect_location(request, default=reverse('admin:index'))
        return cas_views.login(request, redirect_to=redirect_to)

    @never_cache
    def logout(self, request, extra_context=None):
        return cas_views.logout(request)


class CASAdminSite(CASMixin, AdminSite):

    """Admin site that redirects to CAS for login and logout."""


site = AdminSite()
cas_site = CASAdminSite()


def autodiscover(register_to, include_defaults=True):
    # Look through INSTALLED_APPS and import the admin module for
    # each one (if present).
    autodiscover_modules('admin', register_to=register_to)
    # Copy models registered to the default admin site.
    if include_defaults:
        register_to._registry.update(default_admin_site._registry)
