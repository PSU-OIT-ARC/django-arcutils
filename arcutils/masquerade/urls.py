from django.conf.urls import url
from django.http import Http404

from . import views
from .settings import is_enabled


app_name = 'masquerade'


if is_enabled():
    select_view = views.MasqueradeSelectView.as_view()
    masquerade_view = views.MasqueradeView.as_view()
    unmasquerade_view = views.UnmasqueradeView.as_view()
else:
    def _not_found_view(request, *args, **kwargs):
        raise Http404

    select_view = _not_found_view
    masquerade_view = _not_found_view
    unmasquerade_view = _not_found_view


urlpatterns = [
    url(r'^select$', select_view, name='select'),
    url(r'^masquerade$', masquerade_view, name='masquerade'),
    url(r'^unmasquerade$', unmasquerade_view, name='unmasquerade'),
]
