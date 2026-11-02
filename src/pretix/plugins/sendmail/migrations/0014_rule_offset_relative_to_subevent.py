from django.db import migrations, models


def add_offset_relative_to_subevent_if_missing(apps, schema_editor):
    table = "sendmail_rule"
    column = "offset_relative_to_subevent"
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        existing = {
            c.name
            for c in connection.introspection.get_table_description(cursor, table)
        }
    if column in existing:
        return

    Rule = apps.get_model("sendmail", "Rule")
    field = models.BooleanField(default=True)
    field.set_attributes_from_name(column)
    schema_editor.add_field(Rule, field)


class Migration(migrations.Migration):

    dependencies = [
        ("sendmail", "0013_activate_plugin_for_events_with_scheduled_mails"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="rule",
                    name="offset_relative_to_subevent",
                    field=models.BooleanField(default=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    add_offset_relative_to_subevent_if_missing,
                    migrations.RunPython.noop,
                ),
            ],
        ),
    ]
