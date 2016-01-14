from django.forms.models import BaseModelFormSet
from django.forms.formsets import BaseFormSet
from django.forms.utils import ErrorDict


# add some helpful methods to the formset
class FormSetMixin:
    def iter_with_empty_form_first(self):
        """
        Iterates over the forms in this formset, but the first form yielded
        is the empty one. This simplifies the logic in templates, since the
        empty_form is no longer a special case
        """
        yield self.empty_form
        for form in iter(self):
            yield form

    def clean(self):
        """
        When cleaning, if the form is being deleted, any errors on it should be
        ignored
        """
        for form in self.forms:
            # this form is being deleted, so overwrite the errors
            if form.cleaned_data.get("DELETE"):
                form._errors = ErrorDict()


# add the FormSetMixin to the base FormSet classes
class BaseFormSet(FormSetMixin, BaseFormSet):
    pass


class BaseModelFormSet(FormSetMixin, BaseModelFormSet):
    pass
