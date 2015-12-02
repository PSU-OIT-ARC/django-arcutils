from django.conf.urls import url

from . import views
from .settings import is_enabled


app_name = 'masquerade'


if is_enabled():
    urlpatterns = [
        url(r'^select$', views.MasqueradeSelectView.as_view(), name='select'),
        url(r'^masquerade$', views.MasqueradeView.as_view(), name='masquerade'),
        url(r'^unmasquerade$', views.UnmasqueradeView.as_view(), name='unmasquerade'),
    ]
else:
    urlpatterns = []
