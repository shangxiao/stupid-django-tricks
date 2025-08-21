import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Brand",
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
                ("name", models.CharField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
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
                ("sku", models.CharField(unique=True, verbose_name="SKU")),
                ("name", models.CharField()),
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(db_default=models.Value("USD"))),
                (
                    "stock_qty",
                    models.PositiveIntegerField(
                        db_default=models.Value(0), verbose_name="Stock quantity"
                    ),
                ),
                (
                    "availability",
                    models.CharField(
                        choices=[
                            ("in_stock", "In Stock"),
                            ("preorder", "Preorder"),
                            ("discontinued", "Discontinued"),
                        ],
                        db_default=models.Value("in_stock"),
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_default=models.Value(True), verbose_name="Active?"
                    ),
                ),
                ("created_at", models.DateTimeField(verbose_name="Created at")),
                ("updated_at", models.DateTimeField(verbose_name="Updated at")),
                (
                    "brand",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pg_copy.brand",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pg_copy.category",
                    ),
                ),
            ],
        ),
    ]
