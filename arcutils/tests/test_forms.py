from django.test import TestCase
from django.forms.utils import ErrorDict

from arcutils.forms import FormSetMixin


class Form:

    pass


class EmptyForm(Form):

    pass


class BaseFormSet:

    # Mocks Django's BaseFormSet

    def __init__(self, forms=[]):
        self.empty_form = EmptyForm()
        self.forms = forms or [Form(), Form()]

    def __iter__(self):
        return iter(self.forms)

    def clean(self):
        pass


class FormSet(FormSetMixin, BaseFormSet):

    pass


class TestFormSetMixin(TestCase):

    def test_iter_with_empty_form_first(self):
        """Ensure the empty form is included first."""
        formset = FormSet()
        forms = list(formset.iter_with_empty_form_first())
        self.assertEqual(len(forms), 3)
        self.assertIsInstance(forms[0], EmptyForm)
        self.assertIsInstance(forms[1], Form)
        self.assertIsInstance(forms[2], Form)

    def test_clean(self):
        form_a = Form()
        form_a.cleaned_data = {'DELETE': True}
        form_a._errors = ErrorDict(name='That is not a valid name')

        form_b = Form()
        form_b.cleaned_data = {'name': 'John'}
        form_b._errors = ErrorDict()

        form_c = Form()
        form_c.cleaned_data = {}
        form_c._errors = ErrorDict(name='That is not a valid name')

        formset = FormSet(forms=[form_a, form_b, form_c])
        formset.clean()

        self.assertEqual(form_a._errors, ErrorDict())
