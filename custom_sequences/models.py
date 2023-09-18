from django.db import models
from django.db.models.constraints import BaseConstraint
from django.db.models.expressions import Func, Value


class CreateSequenceConstraint(BaseConstraint):
    def __init__(self, *, name: str, start: int = None, increment: int = None):
        super().__init__(name=name)
        self.start = start
        self.increment = increment

    def constraint_sql(self, model, schema_editor):
        return None

    def create_sql(self, model, schema_editor):
        name = schema_editor.quote_name(self.name)
        sql = f"CREATE SEQUENCE IF NOT EXISTS {name}"
        if self.start:
            sql += f" START WITH {self.start}"
        if self.increment:
            sql += f" INCREMENT BY {self.increment}"
        return sql

    def remove_sql(self, model, schema_editor):
        name = schema_editor.quote_name(self.name)
        return f"DROP SEQUENCE IF EXISTS {name}"

    def validate(self, *args, **kwargs):
        return True

    def __eq__(self, other):
        if isinstance(other, CreateSequenceConstraint):
            return (
                self.name == other.name
                and self.start == other.start
                and self.increment == other.increment
            )

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["name"] = self.name
        kwargs["start"] = self.start
        kwargs["increment"] = self.increment
        return path, args, kwargs


class Sequence(Func):
    function = "nextval"
    allowed_default = True

    def __init__(self, name):
        super().__init__(Value(name))


class SequenceField(models.IntegerField):
    def __init__(self, sequence_name, *args, **kwargs):
        self.sequence_name = sequence_name
        kwargs["db_default"] = Sequence(sequence_name)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = [self.sequence_name] + args
        return name, path, args, kwargs


class ModelWithMultipleSequenceFields(models.Model):
    sequence_1 = SequenceField("test_sequence", primary_key=True)
    sequence_2 = SequenceField("starts_10_increments_5")

    class Meta:
        constraints = [
            CreateSequenceConstraint(name="test_sequence"),
            CreateSequenceConstraint(
                name="starts_10_increments_5", start=10, increment=5
            ),
        ]
