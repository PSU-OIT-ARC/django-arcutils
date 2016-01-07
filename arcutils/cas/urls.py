"""Default URLs for CAS.

Hook them into your app like so::

    # Top level urls.py (typically)
    import arcutils.cas.urls

    urlpatterns = [
        url(r'^account/', include(arcutils.cas.urls)),
    ]

"""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^login$', views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^cas/validate$', views.validate, name='cas-validate'),
]
