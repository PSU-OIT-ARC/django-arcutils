from collections import Sequence

from rest_framework.renderers import TemplateHTMLRenderer


class TemplateHTMLContextDictRenderer(TemplateHTMLRenderer):

    """Wrap serialized data in a dictionary for use in templates.

    Otherwise, the serialized data gets dumped into the template context
    without any namespacing.

    The serialized data will be wrapped in a context dictionary like so
    if the data is a list::

        {'object_list': data}

    Or like this if the data is a dict::

        {'object': data}

    To use a different context object name, set ``context_object_name``
    on the relevant view class::

        class PantsView(ListAPIView):

            # Access data via pants instead of object_list in template
            context_object_name = 'pants'
            template_name = 'pants/list.html'

    .. note:: If ``context_object_name`` is set to a name that's set by
              a context processor (like ``request`` or ``user``), the
              serialized data will be shadowed and unavailable in the
              template.

    """

    def resolve_context(self, data, request, response):
        view = response.renderer_context['view']
        default_name = 'object_list' if isinstance(data, Sequence) else 'object'
        context_object_name = getattr(view, 'context_object_name', default_name)
        data = {context_object_name: data}
        return super().resolve_context(data, request, response)
