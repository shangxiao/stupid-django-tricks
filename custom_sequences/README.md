Custom Model Sequence Fields
============================

September 2023


Django 5.0 introduces a long-awaited useful feature `db_default` to allow us to specify database-level defaults for our
model fields. Beyond the immediate advantages we can also use it to define custom, sequences in addition to `AutoField`,
which has, until now, been something that was not possible.

For PostgreSQL, we have the option of defining sequences in a few ways, one of which is to simply declare the default
with the expression using the `nextval()` function.


```python
class SequencedModel(Model):
    a_sequence = IntegerField(db_default=RawSQL("nextval('sequence_name')", params=[]))
```

For something a little more formal we can define a custom `Field`, `Func` & setup a constraint to declare the sequence:

```python
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

class SequenceField(IntegerField):
    def __init__(self, sequence_name, *args, **kwargs):
        self.sequence_name = sequence_name
        kwargs["db_default"] = Sequence(sequence_name)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = [self.sequence_name] + args
        return name, path, args, kwargs
```

then use it like so:


```python
class SequencedModel(Model):
    a_sequence = SequenceField("a_sequence")

    class Meta:
        constraints = [
            SequenceConstraint(name="a_sequence", start=10, increment=5)
        ]
```

**Caveat:** Constraints are added _after_ model creation meaning that if we were to simply make migrations as-is then
the migration will fail as the database requires the sequence to be created beforehand. The fix is to add the
constraint, then add the field (or alter) in a later migration.
