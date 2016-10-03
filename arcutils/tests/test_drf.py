from unittest import TestCase

from arcutils.drf import TemplateHTMLContextDictRenderer


class Base:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class View(Base):

    pass


class Request(Base):

    pass


class Response(Base):

    exception = None
    renderer_context = {
        'view': View(),
    }


class TestDRF(TestCase):

    def setUp(self):
        self.renderer = TemplateHTMLContextDictRenderer()

    def check_context(self, data, wrapper_name, request=None, response=None, view=None):
        request = request or Request()
        response = response or Response()
        view = view or View()
        renderer_context = {
            'request': request,
            'response': response,
            'view': view,
        }
        context = self.renderer.get_template_context(data, renderer_context)
        self.assertIn(wrapper_name, context)
        self.assertIs(context[wrapper_name], data)

    def test_template_html_context_renderer_with_dict(self):
        self.check_context({}, 'object')

    def test_template_html_context_renderer_with_list(self):
        self.check_context([], 'object_list')

    def test_template_html_context_renderer_with_dict_and_custom_wrapper_name(self):
        view = View(context_object_name='pants')
        self.check_context({}, 'pants', view=view)

    def test_template_html_context_renderer_with_list_and_custom_wrapper_name(self):
        view = View(context_object_name='horse')
        self.check_context([], 'horse', view=view)

    def test_template_html_context_renderer_with_custom_wrapper_names(self):
        view = View(context_object_name='horse', context_object_list_name='horses')
        self.check_context({}, 'horse', view=view)
        self.check_context([], 'horses', view=view)
