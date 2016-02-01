from django.conf import settings


def defaults(request):
    return {
        'PROJECT': settings.PROJECT,
    }
