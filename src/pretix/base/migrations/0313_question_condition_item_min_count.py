# Generated manually for Caught order-level question conditions

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pretixbase", "0312_voucher_display_only"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="condition_item",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Leave empty to always ask this order-level question. If set, the question is only shown when "
                    "the selected product is in the order at least as often as the minimum quantity below."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="conditioned_order_questions",
                to="pretixbase.item",
                verbose_name="Only ask if this product is ordered",
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="condition_min_count",
            field=models.PositiveIntegerField(
                default=1,
                help_text=(
                    "Only applies when a product is selected above. Example: set to 5 to ask the question only when "
                    "that product is ordered at least 5 times."
                ),
                verbose_name="Minimum quantity of that product",
            ),
        ),
    ]
