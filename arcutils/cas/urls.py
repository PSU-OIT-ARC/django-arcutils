"""Default URLs for CAS.

Hook them into your app like so::

    # Top level urls.py (typically)
    import arcutils.cas.urls

    urlpatterns = [
        url(r'^account/', include(arcutils.cas.urls)),
    ]

"""
import cas

from django.conf.urls import url

urlpatterns = [
    url(r'^login$', cas.views.login, name='login'),
    url(r'^logout$', cas.views.logout, name='logout'),
]
