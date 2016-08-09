from collections import Sequence

from rest_framework.renderers import TemplateHTMLRenderer


class TemplateHTMLContextDictRenderer(TemplateHTMLRenderer):

    """Wrap serialized data in a dictionary for use in templates.

    Otherwise, the serialized data will get dumped into the template
    context without any namespacing.

    The serialized data will be wrapped in a context dictionary like
    this if the data is a list (or any other sequence type)::

        {'object_list': data}

    or like this if the data is a dict (or any other non-sequence
    type)::

        {'object': data}

    To use a different wrapper name, set ``context_object_name`` on the
    relevant view class::

        class PantsView(ListAPIView):

            # Access data via ``pants`` instead of ``object_list`` in
            # template.
            context_object_name = 'pants'
            template_name = 'pants/list.html'

    For view classes that have some methods that return lists and others
    that return objects (e.g., ``ViewSets``), lists can be wrapped using
    a different name by setting ``context_object_list_name``::

        class HorseViewSet(ViewSet):

            context_object_name = 'horse'
            context_object_list_name = 'horses'

    .. note:: If ``context_object_list_name`` or ``context_object_name``
              is set to a name that's also set by a context processor
              (like ``request`` or ``user``), the serialized data will
              be shadowed and inaccessible in the template.

    """

    context_object_name = 'object'
    context_object_list_name = 'object_list'

    def get_template_context(self, data, renderer_context):
        wrapper_name = self.get_wrapper_name(data, renderer_context)
        data = {wrapper_name: data}
        return super().get_template_context(data, renderer_context)

    def get_wrapper_name(self, data, renderer_context):
        view = renderer_context['view']
        if isinstance(data, Sequence):
            name = (
                getattr(view, 'context_object_list_name', None) or
                getattr(view, 'context_object_name', None) or
                self.context_object_list_name
            )
        else:
            name = (
                getattr(view, 'context_object_name', None) or
                self.context_object_name
            )
        return name
