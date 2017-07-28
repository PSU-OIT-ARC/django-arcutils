from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auditor', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='auditlog',
            options={'ordering': ['-timestamp', 'changeset_id', 'sequence']},
        ),
    ]
