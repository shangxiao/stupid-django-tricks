from django.db import migrations, models

from mock_now.models import create_view, drop_view


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Now",
            fields=[
                ("now", models.DateTimeField(primary_key=True, serialize=False)),
            ],
            options={
                "db_table": "now_view",
                "managed": False,
            },
        ),
        migrations.RunSQL(sql=create_view, reverse_sql=drop_view, elidable=False),
    ]
