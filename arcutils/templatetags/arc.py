from bootstrapform.templatetags.bootstrap import *
from django.template import Template, Context, Library
from django.template.loader import get_template
from django.utils.safestring import mark_safe

register = Library()
