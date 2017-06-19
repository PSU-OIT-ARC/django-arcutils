import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.postgres.fields.jsonb


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('changeset_id', models.UUIDField()),
                ('sequence', models.PositiveIntegerField()),
                ('message', models.CharField(max_length=255)),
                ('object_id', models.CharField(max_length=255)),
                ('created', models.BooleanField()),
                ('deleted', models.BooleanField()),
                ('field_name', models.CharField(max_length=255)),
                ('old_value', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('new_value', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['timestamp', 'changeset_id', 'sequence'],
            },
        ),
    ]
