import itertools

from django.forms import models
from django.forms import formsets
from django.forms.utils import ErrorDict


class FormSetMixin:

    """Adds a couple helpful methods to FormSets."""

    def iter_with_empty_form_first(self):
        """Yield an empty form and then the forms in the FormSet.

        This simplifies formset logic in templates, since the empty form
        is no longer a special case.

        """
        return itertools.chain((self.empty_form,), self)

    def clean(self):
        """Ignore errors on forms that are being deleted."""
        for form in self:
            if form.cleaned_data.get('DELETE'):
                form._errors = ErrorDict()
        super().clean()


class BaseFormSet(FormSetMixin, formsets.BaseFormSet):

    pass


class BaseModelFormSet(FormSetMixin, models.BaseModelFormSet):

    pass
