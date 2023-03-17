from django.db import models
from django.db.models.constraints import UniqueConstraint

from abusing_constraints.constraints import Callback, ForeignKeyConstraint, RawSQL, View


class Tenant(models.Model):
    ...


class Foo(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                name="tenant_constraint_target",
                fields=["id", "tenant"],
            )
        ]


class Bar(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    foo = models.ForeignKey(Foo, null=True, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            ForeignKeyConstraint(
                name="tenant_constraint",
                fields=["foo", "tenant"],
                to_model="Foo",
                to_fields=["id", "tenant"],
            ),
        ]


data_stored_procedure = """\
CREATE OR REPLACE PROCEDURE data_stored_procedure()
LANGUAGE SQL
AS $$
INSERT INTO data (data) VALUES (99);
$$
"""

drop_data_stored_procedure = """\
DROP PROCEDURE IF EXISTS data_stored_procedure CASCADE
"""


def initial_data(model, schema_editor):
    # (here model is fake)
    queryset = model._default_manager.using(schema_editor.connection.alias)
    queryset.delete()
    queryset.bulk_create(
        [
            model(data=1),
            model(data=2),
            model(data=3),
        ]
    )


def reverse_initial_data(model, schema_editor):
    ...


class Data(models.Model):
    data = models.IntegerField()

    class Meta:
        db_table = "data"
        constraints = [
            RawSQL(
                name="data_stored_procedure",
                sql=data_stored_procedure,
                reverse_sql=drop_data_stored_procedure,
            ),
            Callback(
                name="initial_data",
                callback=initial_data,
                reverse_callback=reverse_initial_data,
            ),
        ]


class Document(models.Model):
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

    class Meta:
        constraints = []


Document._meta.constraints += [
    View(
        name="active_documents",
        query=Document.objects.filter(is_archived=False).values("id", "name"),
    ),
]


class ActiveDocument(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "active_documents"
        managed = False
