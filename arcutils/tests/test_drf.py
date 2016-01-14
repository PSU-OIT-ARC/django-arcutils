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

    def check_context(self, data, wrapper_name, request=None, response=None):
        request = request or Request()
        response = response or Response()
        context = self.renderer.resolve_context(data, request, response)
        self.assertIn(wrapper_name, context)
        self.assertIs(context[wrapper_name], data)

    def test_template_html_context_renderer_with_dict(self):
        self.check_context({}, 'object')

    def test_template_html_context_renderer_with_list(self):
        self.check_context([], 'object_list')

    def test_template_html_context_renderer_with_dict_and_custom_wrapper_name(self):
        view = View(context_object_name='pants')
        response = Response(renderer_context={
            'view': view,
        })
        self.check_context({}, 'pants', response=response)

    def test_template_html_context_renderer_with_list_and_custom_wrapper_name(self):
        view = View(context_object_name='horse')
        response = Response(renderer_context={
            'view': view,
        })
        self.check_context([], 'horse', response=response)

    def test_template_html_context_renderer_with_custom_wrapper_names(self):
        view = View(context_object_name='horse', context_object_list_name='horses')
        response = Response(renderer_context={
            'view': view,
        })
        self.check_context({}, 'horse', response=response)
        self.check_context([], 'horses', response=response)
