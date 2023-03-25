Defining Check Constraints from Model Fields
============================================

March 2023


With [Having Fun with Constraints](../abusing_constraints/README.md) we see how Django constraints add constraint
support to our models.

Adding check constraints from our model fields is also possible.

Defining constraints on model fields has some advantages:

 - Code colocality
 - Field & check are bundled together - encouraging code reuse


Making use of `db_check()`
--------------------------

Django has long since (privately) supported defining check constraints on fields with the undocumented `db_check()`
method. Fields with this implemented add a `CHECK` clause to columns when present during model creation or
an `ALTER TABLE ... ADD CONSTRAINT` operation when fields are added to an existing model. We can observe this
by defining a `PositiveIntegerField` on our models then inspecting the resulting schema in Postgres to see a check
constraint created to enforce values >= 0.

In PostgreSQL it's worth noting at that there is no difference between column-level & table-level check constraints - they're just different
places within a `CREATE TABLE` to define the same thing. Additionally, while not encouraged for SQL compatibility,
[PostgreSQL supports referring to other columns in a column check constraint](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-CHECK-CONSTRAINTS).

We can use this method to define our fields to accept a check parameter as a Q object then compile the Q against the model:

```python
class ColumnCheckMixin:
    def __init__(self, *args, check=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_check = check

    def db_check(self, connection):
        query = Query(self.model)
        query.add_q(self.column_check)
        compiler = query.get_compiler(using=connection.alias)
        sql, params = query.where.as_sql(compiler, connection.alias)
        with connection.cursor() as cursor:
            return cursor.mogrify(sql, params).decode("utf-8")

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["check"] = self.column_check
        return name, path, args, kwargs
```

If we want to support `validate_constraints()` on model instances then we could add a dummy constraint to the field's
models:

```python
class ColumnCheckConstraint(CheckConstraint):
    # Define a "dummy" constraint that just implements validation

    def constraint_sql(self, model, schema_editor):
        return None

    def create_sql(self, model, schema_editor):
        return None

    def remove_sql(self, model, schema_editor):
        return None


class ColumnCheckMixin:
    # Then add this dummy constraint to the model via contribute_to_class():

    def contribute_to_class(self, cls, name, private_only=False):
        if self.column_check:
            cls._meta.constraints.append(
                ColumnCheckConstraint(check=self.column_check, name=f"check_{name}")
            )
        super().contribute_to_class(cls, name, private_only)
```

This mixin is then used like so:

```python
class CheckedIntegerField(ColumnCheckMixin, models.IntegerField):
    ...

class Project(models.Model):
    percentage = CheckedIntegerField(check=Q(percentage__gte=0, percentage__lte=100))
```


Adding a CheckConstraint to the Model from the Field
----------------------------------------------------

And to round things off, we also have the option of foregoing `db_check()` and simply adding an instance
of `CheckConstraint` to the list of constraints, although this does require an additional hack.
Models store the original user-defined options
on the meta in a separate dictionary called `original_attrs` and this is used by the migration autodetector to determine the model
state to migrate towards. Updating the constraints attribute is not enough, we must also update `original_attrs`:

```python
class ColumnCheckMixin:
    # Using a regular CheckConstraint in lieu of defining db_check() to create a table check constraint:

    def contribute_to_class(self, cls, name, private_only=False):
        # Create the check as a table check constraint.
        if self.column_check:
            constraint = CheckConstraint(check=self.column_check, name=f"check_{name}")
            cls._meta.constraints += [constraint]
            # XXX We must also update the meta's original_attrs attribute in order to get migrations to pick it up.
            if "constraints" in cls._meta.original_attrs:
                cls._meta.original_attrs["constraints"] += [constraint]
            else:
                cls._meta.original_attrs["constraints"] = [constraint]
        super().contribute_to_class(cls, name, private_only)
```

See the code & tests for the full example.
