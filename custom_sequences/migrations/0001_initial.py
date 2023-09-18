from django.db import migrations, models

import custom_sequences.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ModelWithMultipleSequenceFields",
            fields=[
                ("sequence_1", models.IntegerField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.AddConstraint(
            model_name="modelwithmultiplesequencefields",
            constraint=custom_sequences.models.CreateSequenceConstraint(
                increment=None, name="test_sequence", start=None
            ),
        ),
        migrations.AddConstraint(
            model_name="modelwithmultiplesequencefields",
            constraint=custom_sequences.models.CreateSequenceConstraint(
                increment=5, name="starts_10_increments_5", start=10
            ),
        ),
        migrations.AddField(
            model_name="modelwithmultiplesequencefields",
            name="sequence_2",
            field=custom_sequences.models.SequenceField(
                "starts_10_increments_5",
                db_default=custom_sequences.models.Sequence("starts_10_increments_5"),
            ),
        ),
        migrations.AlterField(
            model_name="modelwithmultiplesequencefields",
            name="sequence_1",
            field=custom_sequences.models.SequenceField(
                "test_sequence",
                db_default=custom_sequences.models.Sequence("test_sequence"),
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
