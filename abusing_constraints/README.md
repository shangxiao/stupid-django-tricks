Having Fun with Constraints
===========================

March 2023


Introduction to Constraints
---------------------------

[Django constraints](https://docs.djangoproject.com/en/4.1/ref/models/constraints/) allow you to add different types of table-level database
constraints to your models.

Django currently supports check & unique constraints. Both of these extend from `BaseConstraint` which provide the
necessary hooks for forwards/reverse migrations, makemigrations as well as validation of constraints from model & form instances.

A Django constraint follows this basic pattern:

```python
class CustomConstraint(BaseConstraint):
    def __init__(self, *, name, custom_param, violation_error_message=None):
        # define your custom params as needed, be sure to pass name & violation_error_message to BaseConstraint
        super().__init__(name, violation_error_message)
        self.custom_param = custom_param

    def constraint_sql(self, model, schema_editor):
        # Used by migrations to define the constraint when included within CREATE TABLE
        # Eg: CHECK price > 0
        # Note: model is fake

    def create_sql(self, model, schema_editor):
        # Used by migrations to define the constraint when included with ALTER TABLE
        # Eg: ALTER TABLE table ADD CONSTRAINT name CHECK price > 0
        # Note: model is fake

    def remove_sql(self, model, schema_editor):
        # Used for reverse migrations and done within ALTER TABLE
        # Eg: ALTER TABLE table DROP CONSTRAINT name
        # Note: model is fake

    def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        # Validation done as part of model or form validation ie instance.validate_constraints()
        # The model passed here is a real model. Use any database query as needed to verify the constraint.
        # Validation failure must raise a ValidationError.
        # Eg: Q(...filtering_as_required...).check() -> fail then raise ValidationError

    def __eq__(self):
        # You *must* define this in order to prevent makemigrations from recreating your constraint migration operations.
        if isinstance(other, CustomConstraint):
            return (
                self.name == other.name
                and self.custom_param == other.custom_param
                and self.violation_error_message == other.violation_error_message
            )
        return super().__eq__(other)

    def deconstruct(self):
        # You must extend this to include additional params passed to __init__() for serialisation purposes.
        path, args, kwargs = super().deconstruct()
        kwargs["custom_param"] = self.custom_param
        return path, args, kwargs
```



We can extend the supplied `BaseConstraint` in interesting ways:


Custom Constraint: Foreign Keys
-------------------------------

### Defining composite foreign keys to enforce tenancy equality in multi-tenancy databases

Django's foreign keys are basic single-column keys with primary key references. Sometimes we may want more complex foreign keys, like using
composite keys in multi-tenanted databases to enforce tenancy across relationships.

Take the following trivial multi-tenancy design where tenanted models `Foo` and `Bar` are related with a foreign key:

```python
class Tenant(models.Model):
    ...

class Foo(models.Model):
    tenant = models.ForeignKey(Tenant, ...)

class Bar(models.Model):
    tenant = models.ForeignKey(Tenant, ...)
    foo = models.ForeignKey(Foo, ...)
```

Adding an **extra** composite foreign key from `Bar` to `Foo`, with the tenant as part of the key, **enforces** tenant equality. ie
the foreign key now prevents relationships from existing where Foo and Bar belong to different tenants.

To do this 2 steps are required:

1. Create a unique index on the referenced model, Foo, for the key to target that will include the primary key + tenant: `(id, tenant_id)`
2. Add a supplementary foreign key on the referencing model, Bar, to reference the newly created index.

```python
class Tenant(models.Model):
    ...

class Foo(models.Model):
    tenant = models.ForeignKey(Tenant)

    class Meta:
        constraints = [
            UniqueConstraint(columns=["id", "tenant"], ...)
        ]

class Bar(models.Model):
    tenant = models.ForeignKey(Tenant, ...)
    foo = models.ForeignKey(Foo, ...)

    class Meta:
        constraints = [
            ForeignKeyConstraint(
                columns=["foo_id", "tenant_id"],
                to_table="abusing_constraints_foo",
                to_columns=["id", "tenant_id"],
                ...
            ),
        ]
```

This new foreign key constraint is a simple extension of `BaseConstraint` (note this is a simple implementation without
any proper quoting of names, etc for demonstration purposes):

```python
class ForeignKeyConstraint(BaseConstraint):
    def __init__(
        self,
        *,
        name,
        columns,
        to_table,
        to_columns,
        on_delete=None,
        on_update=None,
        violation_error_message=None,
    ):
        super().__init__(name, violation_error_message=violation_error_message)
        self.columns = columns
        self.to_table = to_table
        self.to_columns = to_columns
        self.on_delete = on_delete
        self.on_update = on_update

    def create_sql(self, model, schema_editor):
        table = model._meta.db_table
        constraint_sql = self.constraint_sql(model, schema_editor)
        return f"ALTER TABLE {table} ADD CONSTRAINT {self.name} {constraint_sql}"

    def remove_sql(self, model, schema_editor):
        table = model._meta.db_table
        return f"ALTER TABLE {table} DROP CONSTRAINT {self.name}"

    def constraint_sql(self, model, schema_editor):
        columns = ", ".join(self.columns)
        to_columns = ", ".join(self.to_columns)
        on_delete = f"ON DELETE {self.on_delete}" if self.on_delete else ""
        on_update = f"ON UPDATE {self.on_update}" if self.on_update else ""
        return f"FOREIGN KEY ({columns}) REFERENCES {self.to_table} ({to_columns}) {on_delete} {on_update}"

    def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        with connection.cursor() as cursor:
            # to keep things simple assume each field doesn't have a separate column name
            where_clause = " AND ".join(
                f"{field} = %({field})s" for field in self.to_columns
            )
            params = {
                field: getattr(instance, self.columns[i])
                for i, field in enumerate(self.to_columns)
            }
            table = self.to_table
            cursor.execute(f"SELECT count(*) FROM {table} WHERE {where_clause}", params)
            result = cursor.fetchone()
            if result[0] == 0:
                raise ValidationError(self.get_violation_error_message())

    def __eq__(self, other):
        if isinstance(other, ForeignKeyConstraint):
            return (
                self.name == other.name
                and self.violation_error_message == other.violation_error_message
                and self.columns == other.columns
                and self.to_table == other.to_table
                and self.to_columns == other.to_columns
                and self.on_delete == other.on_delete
                and self.on_update == other.on_update
            )
        return super().__eq__(other)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["to_table"] = self.to_table
        kwargs["columns"] = self.columns
        kwargs["to_columns"] = self.to_columns
        kwargs["on_delete"] = self.on_delete
        kwargs["on_update"] = self.on_update
        return path, args, kwargs
```


Database-Level Cascading Deletes
--------------------------------

Notice in the `ForeignKeyConstraint` class above I made provision for cascading updates & deletes - if you wish to have
database-level cascades implemented you can use this supplementary foreign key to do that:

 1. Specify `DO_NOTHING` for the main ForeignKey
 2. Add the supplementary foreign key specifying database-level cascades

```python
class Parent(models.Model):
    ...

class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.DO_NOTHING)

    class Meta:
        constraints = [
            ForeignKeyConstraint(
                name="native_on_delete",
                columns=["parent_id"],
                to_table="abusing_constraints_parent",
                to_columns=["id"],
                on_delete="CASCADE",
            ),
        ]
```


Creating Arbitrary Database Artifacts
-------------------------------------

> Constraints provide the ability to inject any database query – DDL or DML – into your migrations

Things get interesting when we realise that constraints become a point where we can add custom database operations to our migrations as an alternative
to the manual `RunPython` or `RunSQL` migration operations.


### A RawSQL Constraint

```python
class RawSQL(BaseConstraint):
    def __init__(self, *, name, sql, reverse_sql):
        super().__init__(name)
        self.sql = sql
        self.reverse_sql = reverse_sql

    def create_sql(self, model, schema_editor):
        return self.sql

    def remove_sql(self, model, schema_editor):
        return self.reverse_sql

    # These 2 methods don't apply for non-constraints

    def constraint_sql(self, model, schema_editor):
        return None

    def validate(self, *args, **kwargs):
        return True

    # ...other methods similarly defined as above
```

Here's what we can do with this:

### Example: Stored Procedures

Define a stored procedure for your model within the model's meta 😆

```python
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
        ]
```

### A Callback Constraint

An example with simple forwarding of the fake model & schema editor, noting that we need to **serialise**
the callbacks in order for it to be injected into your migrations. Obviously this limits what you can do but
it is possible for simple functions:

```python
class Callback(BaseConstraint):
    def __init__(self, *, name, callback, reverse_callback):
        super().__init__(name)
        self.callback = (
            marshal.dumps(callback.__code__) if callable(callback) else callback
        )
        self.reverse_callback = (
            marshal.dumps(reverse_callback.__code__)
            if callable(reverse_callback)
            else reverse_callback
        )

    def create_sql(self, model, schema_editor):
        code = marshal.loads(self.callback)
        forwards = types.FunctionType(code, globals(), "forwards")
        forwards(model, schema_editor)

    def remove_sql(self, model, schema_editor):
        code = marshal.loads(self.reverse_callback)
        reverse = types.FunctionType(code, globals(), "reverse")
        reverse(model, schema_editor)

    # ...other methods similarly defined as above
```

### Example: Initial data

Using the callback constraint to define initial model data:

```python
def initial_data(model, schema_editor):
    # (here model is fake)
    queryset = model._default_manager.using(schema_editor.connection.alias)
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
        constraints = [
            Callback(
                name="initial_data",
                callback=initial_data,
                reverse_callback=reverse_initial_data,
            ),
        ]
```


Something More Useful: Views
----------------------------

Database views are a useful abstraction and a common method for using them in Django is to create the view in a migration,
then create an unmanaged model that refers to the view using `Meta.db_table`.

To avoid the hassle of manual migrations an extension of constraints like so can be used (noting that constraints will only
be applied to managed models):

```python
class Document(models.Model):
    # This is the main document model
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

    class Meta:
        constraints = []

Document._meta.constraints += [
    View(
        name="active_documents",
        # Remember to forward the primary key (or create one)
        query=Document.objects.filter(is_archived=False).values("id", "name"),
    ),
]

class ActiveDocument(models.Model):
    # Model representing our database view "active_documents"
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "active_documents"
        managed = False
```

**Bonus advantage:** Simple PostgreSQL views like this are **automatically updatable** meaning that any save operations from Django will work!

Here's what the `View` "constraint" could look like:

```python
class View(BaseConstraint):
    def __init__(self, *, name, query):
        super().__init__(name)
        if isinstance(query, str):
            self.query = query
        else:
            # Better to parameterise correctly as __str__() just fills in placeholders
            # without any correct quoting for strings, etc.
            self.query = str(query.query)

    def create_sql(self, model, schema_editor):
        return f"CREATE OR REPLACE VIEW {self.name} AS {self.query}"

    def remove_sql(self, model, schema_editor):
        return f"DROP VIEW IF EXISTS {self.name} CASCADE"

    # ...other methods similarly defined as above
```


Further Reading
---------------
See the [tests & code](.) for complete examples.
