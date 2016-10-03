from rest_framework.routers import (
    DefaultRouter as BaseDefaultRouter,
    Route,
    DynamicListRoute,
    DynamicDetailRoute,
)


# This was copied from rest_framework.routes.SimpleRouter. The list
# routes are unmodified, so they will have trailing slashes as
# usual. The detail routes were modified so that they won't have
# trailing slashes.
ROUTES = [
    # List
    Route(
        url=r'^{prefix}{trailing_slash}$',
        mapping={
            'get': 'list',
            'post': 'create'
        },
        name='{basename}-list',
        initkwargs={'suffix': 'List'}
    ),
    DynamicListRoute(
        url=r'^{prefix}/{methodname}{trailing_slash}$',
        name='{basename}-{methodnamehyphen}',
        initkwargs={}
    ),
    # Detail
    Route(
        url=r'^{prefix}/{lookup}$',
        mapping={
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        },
        name='{basename}-detail',
        initkwargs={'suffix': 'Instance'}
    ),
    DynamicDetailRoute(
        url=r'^{prefix}/{lookup}/{methodname}$',
        name='{basename}-{methodnamehyphen}',
        initkwargs={}
    ),
]


class DefaultRouter(BaseDefaultRouter):

    """A router with a "proper" trailing slash policy.

    Collection/list routes end with a trailing slash; member/detail
    routes don't.

    This is more aesthetically appealing, is arguably more "correct",
    and is easier to use with AngularJS resources.

    """

    routes = ROUTES
