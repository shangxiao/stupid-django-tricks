from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product", models.CharField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("IN_PROGRESS", "In Progress"),
                            ("PAID", "Paid"),
                            ("SHIPPED", "Shipped"),
                            ("DELIVERED", "Delivered"),
                        ]
                    ),
                ),
            ],
        ),
    ]
