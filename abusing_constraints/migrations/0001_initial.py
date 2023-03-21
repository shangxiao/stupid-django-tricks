import django.db.models.deletion
from django.db import migrations, models

import abusing_constraints.constraints


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ActiveDocument",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "active_documents",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="ActiveDocumentByName",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "active_documents_by_name",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Bar",
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
            ],
        ),
        migrations.CreateModel(
            name="Data",
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
                ("data", models.IntegerField()),
            ],
            options={
                "db_table": "data",
            },
        ),
        migrations.CreateModel(
            name="Document",
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
                ("name", models.CharField(max_length=255)),
                ("is_archived", models.BooleanField(default=False)),
            ],
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
            ],
        ),
        migrations.CreateModel(
            name="Foo",
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
                        to="abusing_constraints.tenant",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="document",
            constraint=abusing_constraints.constraints.View(
                is_materialized=False,
                name="active_documents",
                query='SELECT "abusing_constraints_document"."id", "abusing_constraints_document"."name" FROM "abusing_constraints_document" WHERE NOT "abusing_constraints_document"."is_archived"',
            ),
        ),
        migrations.AddConstraint(
            model_name="document",
            constraint=abusing_constraints.constraints.View(
                is_materialized=False,
                name="active_documents_by_name",
                query='SELECT "abusing_constraints_document"."id", "abusing_constraints_document"."name" FROM "abusing_constraints_document" WHERE UPPER("abusing_constraints_document"."name"::text) LIKE UPPER(\'%active%\')',
            ),
        ),
        migrations.AddConstraint(
            model_name="data",
            constraint=abusing_constraints.constraints.RawSQL(
                name="data_stored_procedure",
                reverse_sql="DROP PROCEDURE IF EXISTS data_stored_procedure CASCADE\n",
                sql="CREATE OR REPLACE PROCEDURE data_stored_procedure()\nLANGUAGE SQL\nAS $$\nINSERT INTO data (data) VALUES (99);\n$$\n",
            ),
        ),
        migrations.AddConstraint(
            model_name="data",
            constraint=abusing_constraints.constraints.Callback(
                callback=b"\xe3\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x03\x00\x00\x00\xf3\xe2\x00\x00\x00\x97\x00|\x00j\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|\x01j\x02\x00\x00\x00\x00\x00\x00\x00\x00j\x03\x00\x00\x00\x00\x00\x00\x00\x00\xa6\x01\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00\x00\x00}\x02|\x02\xa0\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa6\x00\x00\x00\xab\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00|\x02\xa0\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00|\x00d\x01\xac\x02\xa6\x01\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00|\x00d\x03\xac\x02\xa6\x01\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00|\x00d\x04\xac\x02\xa6\x01\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00\x00\x00g\x03\xa6\x01\x00\x00\xab\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00d\x00S\x00)\x05N\xe9\x01\x00\x00\x00)\x01\xda\x04data\xe9\x02\x00\x00\x00\xe9\x03\x00\x00\x00)\x06\xda\x10_default_manager\xda\x05using\xda\nconnection\xda\x05alias\xda\x06delete\xda\x0bbulk_create)\x03\xda\x05model\xda\rschema_editor\xda\x08querysets\x03\x00\x00\x00   \xfaK/Users/dsanders/projects/stupid_django_tricks/abusing_constraints/models.py\xda\x0cinitial_datar\x10\x00\x00\x003\x00\x00\x00s|\x00\x00\x00\x80\x00\xe0\x0f\x14\xd4\x0f%\xd7\x0f+\xd2\x0f+\xa8M\xd4,D\xd4,J\xd1\x0fK\xd4\x0fK\x80H\xd8\x04\x0c\x87O\x82O\xd1\x04\x15\xd4\x04\x15\xd0\x04\x15\xd8\x04\x0c\xd7\x04\x18\xd2\x04\x18\xe0\x0c\x11\x88E\x90q\x88M\x89M\x8cM\xd8\x0c\x11\x88E\x90q\x88M\x89M\x8cM\xd8\x0c\x11\x88E\x90q\x88M\x89M\x8cM\xf0\x07\x04\t\n\xf1\x03\x06\x05\x06\xf4\x00\x06\x05\x06\xf0\x00\x06\x05\x06\xf0\x00\x06\x05\x06\xf0\x00\x06\x05\x06\xf3\x00\x00\x00\x00",
                name="initial_data",
                reverse_callback=b"\xe3\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00\xf3\x06\x00\x00\x00\x97\x00d\x00S\x00)\x01N\xa9\x00)\x02\xda\x05model\xda\rschema_editors\x02\x00\x00\x00  \xfaK/Users/dsanders/projects/stupid_django_tricks/abusing_constraints/models.py\xda\x14reverse_initial_datar\x06\x00\x00\x00@\x00\x00\x00s\x07\x00\x00\x00\x80\x00\xd8\x04\x07\x80C\xf3\x00\x00\x00\x00",
            ),
        ),
        migrations.AddField(
            model_name="bar",
            name="foo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="abusing_constraints.foo",
            ),
        ),
        migrations.AddField(
            model_name="bar",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="abusing_constraints.tenant",
            ),
        ),
        migrations.AddConstraint(
            model_name="foo",
            constraint=models.UniqueConstraint(
                fields=("id", "tenant"), name="tenant_constraint_target"
            ),
        ),
        migrations.AddConstraint(
            model_name="bar",
            constraint=abusing_constraints.constraints.ForeignKeyConstraint(
                deferrable=None,
                fields=["foo", "tenant"],
                name="tenant_constraint",
                to_fields=["id", "tenant"],
                to_model="Foo",
            ),
        ),
    ]
