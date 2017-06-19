from collections import namedtuple

from django.apps import apps
from django.db.models.signals import post_delete, post_init, post_save
from django.forms.models import model_to_dict

from arcutils.threadlocals import get_current_request

from .models import AuditLog
from .settings import settings


ModelToAudit = namedtuple('Model', 'name fields model')


def get_models_to_audit():
    specs = settings.get('models', ())
    models = []
    for i, spec in enumerate(specs):
        name = spec['name']
        fields = spec['fields']
        model = apps.get_model(name)

        if not fields:
            raise ValueError('One or more fields must be specified for auditing')

        for field in fields:
            model._meta.get_field(field)

        models.append(ModelToAudit(name, fields, model))

    return models


def connect(app):
    models = get_models_to_audit()
    for (name, fields, model) in models:
        save_current_values = save_current_data_factory(model, fields)
        post_init.connect(save_current_values, sender=model, weak=False)

        add_audit_log_record = add_audit_log_record_factory(model, fields)
        post_save.connect(add_audit_log_record, sender=model, weak=False)

        add_last_audit_log_record = add_last_audit_log_record_factory(model, fields)
        post_delete.connect(add_last_audit_log_record, sender=model, weak=False)


def save_current_data_factory(model, fields):

    def save_current_data(sender, instance, **kwargs):
        data = model_to_dict(instance, fields)
        instance._auditor_data = data

    return save_current_data


def add_audit_log_record_factory(model, fields):

    def add_audit_log_record(sender, instance, created, **kwargs):
        request = get_current_request()

        if request is None:
            return

        def add_record(field_name, old_value, new_value, message):
            AuditLog.objects.create(
                user=info.user,
                timestamp=info.timestamp,
                changeset_id=info.changeset_id,
                sequence=next(info.sequencer),
                message=message,
                object=instance,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                created=created,
                deleted=False,
            )

        info = request.auditor_info
        saved_data = instance._auditor_data

        if created:
            for field in fields:
                message = 'Automatically-detected creation'
                add_record(field, None, getattr(instance, field), message)
        else:
            for field in fields:
                old_val = saved_data[field]
                new_val = getattr(instance, field)
                if old_val != new_val:
                    message = 'Automatically-detected update'
                    add_record(field, old_val, new_val, message)

    return add_audit_log_record


def add_last_audit_log_record_factory(model, fields):

    def add_last_audit_log_record(sender, instance, **kwargs):
        request = get_current_request()

        if request is None:
            return

        def add_record(field_name, old_value, new_value, message):
            AuditLog.objects.create(
                user=info.user,
                timestamp=info.timestamp,
                changeset_id=info.changeset_id,
                sequence=next(info.sequencer),
                message=message,
                object=instance,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                created=False,
                deleted=True,
            )

        info = request.auditor_info

        for field in fields:
            message = 'Automatically-detected deletion'
            add_record(field, getattr(instance, field), None, message)

    return add_last_audit_log_record
