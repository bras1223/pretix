from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sendmail', '0011_remove_cross_event_scheduled_mails_squashed_0012_remove_cross_event_scheduled_mails'),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='offset_relative_to_subevent',
            field=models.BooleanField(default=True),
        ),
    ]
