import abusing_constraints.constraints
import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AccountView",
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
                ("name", models.CharField()),
            ],
            options={
                "db_table": "account_view",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="ProductView",
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
                ("name", models.CharField()),
            ],
            options={
                "db_table": "product_view",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Tenant",
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
                ("name", models.CharField()),
            ],
        ),
        migrations.CreateModel(
            name="User",
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
                ("name", models.CharField()),
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
                ("name", models.CharField()),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="row_level_security_with_views.tenant",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Account",
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
                ("name", models.CharField()),
                (
                    "tenant",
                    models.ForeignKey(
                        db_default=django.db.models.expressions.RawSQL(
                            "nullif(current_setting('app.tenant_id'), '')::int",
                            params=[],
                        ),
                        on_delete=django.db.models.deletion.CASCADE,
                        to="row_level_security_with_views.tenant",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Authorisation",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="row_level_security_with_views.tenant",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="row_level_security_with_views.user",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=abusing_constraints.constraints.View(
                is_materialized=False,
                name="product_view",
                query="select * from row_level_security_with_views_product where tenant_id in (select tenant_id from row_level_security_with_views_authorisation where user_id = nullif(current_setting('app.user', true), '')::int)",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=abusing_constraints.constraints.RawSQL(
                name="check_tenant_id",
                reverse_sql="DROP FUNCTION IF EXISTS check_tenant_id",
                sql="CREATE OR REPLACE FUNCTION check_tenant_id() RETURNS trigger AS $$\nDECLARE\n    myrec record;\nBEGIN\n    SELECT * INTO myrec FROM row_level_security_with_views_authorisation WHERE tenant_id = NEW.tenant_id AND user_id = nullif(current_setting('app.user', true), '')::int;\n    IF FOUND THEN\n        RETURN NEW;\n    END IF;\n    IF nullif(current_setting('app.user', true), '') IS NULL THEN\n        RETURN NEW;\n    END IF;\n    RAISE EXCEPTION 'Not authorised';\nEND\n$$ LANGUAGE plpgsql;\n",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=abusing_constraints.constraints.RawSQL(
                name="product_insert_trigger",
                reverse_sql="DROP TRIGGER IF EXISTS product_insert_trigger ON row_level_security_with_views_product",
                sql="CREATE OR REPLACE TRIGGER product_insert_trigger\nBEFORE insert ON row_level_security_with_views_product\nFOR EACH ROW\nEXECUTE FUNCTION check_tenant_id()\n",
            ),
        ),
        migrations.AddConstraint(
            model_name="account",
            constraint=abusing_constraints.constraints.View(
                is_materialized=False,
                name="account_view",
                query="select * from row_level_security_with_views_account where tenant_id = nullif(current_setting('app.tenant_id', true), '')::int",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="authorisation",
            unique_together={("user", "tenant")},
        ),
    ]
