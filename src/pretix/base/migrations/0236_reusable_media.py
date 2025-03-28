# Generated by Django 3.2.18 on 2023-02-20 12:46

import django.core.serializers.json
import django.db.models.deletion
from django.db import migrations, models

import pretix.base.models.base


def set_can_manage_reusable_media(apps, schema_editor):
    Team = apps.get_model('pretixbase', 'Team')
    Team.objects.filter(can_change_organizer_settings=True).update(can_manage_reusable_media=True)
    Team.objects.filter(can_change_orders=True, all_events=True).update(can_manage_reusable_media=True)


class Migration(migrations.Migration):
    dependencies = [
        ('pretixbase', '0235_auto_20230316_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='media_policy',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='item',
            name='media_type',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='can_manage_reusable_media',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='ReusableMedium',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(max_length=100)),
                ('identifier', models.CharField(max_length=200)),
                ('active', models.BooleanField(default=True)),
                ('expires', models.DateTimeField(blank=True, null=True)),
                ('info', models.JSONField(default=dict)),
                ('notes', models.TextField(null=True, blank=True)),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                               related_name='reusable_media', to='pretixbase.customer')),
                ('linked_giftcard',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_media',
                                   to='pretixbase.giftcard')),
                ('linked_orderposition',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_media',
                                   to='pretixbase.orderposition')),
                ('organizer',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reusable_media',
                                   to='pretixbase.organizer')),
            ],
            options={
                'ordering': ('identifier', 'type', 'organizer'),
                'unique_together': {('identifier', 'type', 'organizer')},
                'index_together': {('identifier', 'type', 'organizer'), ('updated', 'id')},
            },
            bases=(models.Model, pretix.base.models.base.LoggingMixin),
        ),
        migrations.AddField(
            model_name='checkin',
            name='raw_source_type',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.RunPython(
            set_can_manage_reusable_media,
            migrations.RunPython.noop,
        ),
    ]
