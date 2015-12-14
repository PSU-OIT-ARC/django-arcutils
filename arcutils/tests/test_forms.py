from mock import Mock

from django.forms.utils import ErrorDict
from django.test import TestCase

from arcutils.forms import FormSetMixin, BaseFormSet, BaseModelFormSet


class TestFormSetMixin(TestCase):
    def test_iter_with_empty_form_first(self):
        """Ensure it chains the empty_form with the rest of the iterable"""
        fs = FormSetMixin()
        fs.empty_form = 1
        FormSetMixin.__iter__ = lambda cls: iter([2, 3, 4])
        self.assertEqual([1, 2, 3, 4], list(fs.iter_with_empty_form_first()))

    def test_clean(self):
        fs = FormSetMixin()
        form_a = Mock()
        form_a.cleaned_data = {"DELETE": True}
        form_a._errors = ErrorDict({"name": "That's not a valid name"})

        form_b = Mock()
        form_b.cleaned_data = {"name": "John"}
        form_b._errors = ErrorDict()

        form_c = Mock()
        form_c.cleaned_data = {}
        form_c._errors = ErrorDict({"name": "That's not a valid name"})

        fs.forms = [form_a, form_b, form_c]
        fs.clean()
        self.assertEqual(form_a._errors, ErrorDict())

    def test_inheritance(self):
        self.assertTrue(issubclass(BaseFormSet, FormSetMixin))
        self.assertTrue(issubclass(BaseModelFormSet, FormSetMixin))
