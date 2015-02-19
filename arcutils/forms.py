from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.forms.fields import Field
from django.forms.models import BaseModelFormSet
from django.forms.formsets import BaseFormSet
from django.forms.util import ErrorDict
from django import forms


forms.Form.required_css_class = "required"
forms.ModelForm.required_css_class = "required"
Field.required_css_class = "required"

# add some helpful methods to the formset
class FormSetMixin(object):
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
class BaseFormSet(FormSetMixin, BaseFormSet): pass
class BaseModelFormSet(FormSetMixin, BaseModelFormSet): pass


# monkey patch the PasswordResetForm so it indicates if a user does not exist
def _clean_email(self):
    email = self.cleaned_data['email']
    UserModel = get_user_model()
    if not UserModel.objects.filter(email=email, is_active=True).exists():
        raise forms.ValidationError("A user with that email address does not exist!")

    return email

PasswordResetForm.clean_email = _clean_email
