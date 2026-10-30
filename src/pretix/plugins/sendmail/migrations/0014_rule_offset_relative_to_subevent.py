from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sendmail', '0013_activate_plugin_for_events_with_scheduled_mails'),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='offset_relative_to_subevent',
            field=models.BooleanField(default=True),
        ),
    ]
