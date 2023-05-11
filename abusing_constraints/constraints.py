import marshal
import types

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.backends.ddl_references import Columns, Statement, Table
from django.db.models import Model, Q
from django.db.models.constraints import BaseConstraint
from django.db.models.fields.related import resolve_relation
from django.db.models.query import QuerySet
from django.db.utils import DEFAULT_DB_ALIAS


class BasicForeignKeyConstraint(BaseConstraint):
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
        if isinstance(other, BasicForeignKeyConstraint):
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


class ForeignKeyConstraint(BaseConstraint):
    def __init__(
        self,
        *,
        name,
        fields,
        to_model,
        to_fields,
        deferrable=None,
        violation_error_message=None,
    ):
        super().__init__(name, violation_error_message=violation_error_message)
        self.fields = fields
        self.to_model = to_model
        self.to_fields = to_fields
        self.deferrable = deferrable

    def get_to_model(self, from_model):
        return (
            apps.get_model(resolve_relation(from_model, self.to_model))
            if isinstance(self.to_model, str)
            else self.to_model
        )

    def create_sql(self, model, schema_editor):
        sql = schema_editor.sql_create_fk
        table = Table(model._meta.db_table, schema_editor.quote_name)
        name = schema_editor.quote_name(self.name)
        column_names = [
            model._meta.get_field(field_name).get_attname()
            for field_name in self.fields
        ]
        columns = Columns(table, column_names, schema_editor.quote_name)
        to_model = self.get_to_model(model)
        to_table = Table(to_model._meta.db_table, schema_editor.quote_name)
        to_column_names = [
            to_model._meta.get_field(field_name).get_attname()
            for field_name in self.to_fields
        ]
        to_columns = Columns(to_table, to_column_names, schema_editor.quote_name)
        deferrable = schema_editor._deferrable_constraint_sql(self.deferrable)
        return Statement(
            sql,
            table=table,
            name=name,
            column=columns,
            to_table=to_table,
            to_column=to_columns,
            deferrable=deferrable,
        )

    def remove_sql(self, model, schema_editor):
        table = schema_editor.connection.ops.quote_name(model._meta.db_table)
        name = schema_editor.quote_name(self.name)
        return Statement(
            schema_editor.sql_delete_fk,
            table=table,
            name=name,
        )

    def constraint_sql(self, model, schema_editor):
        # It's unclear whether this is ever actually used.... it's called from the CreateModel operation however
        # constraints are added in a separate operation AddConstraint.
        return None

    def get_value(self, value):
        # Deal with allowing either field name referring to the related object or the foreign key value
        if isinstance(value, Model):
            return value.pk
        return value

    def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        to_model = self.get_to_model(model)
        queryset = to_model._default_manager.using(using)
        filters = [
            Q(
                **{
                    model._meta.get_field(field_name).target_field.name: self.get_value(
                        getattr(instance, field_name)
                    )
                }
            )
            for field_name in self.fields
        ]
        if not queryset.filter(*filters).exists():
            raise ValidationError(self.get_violation_error_message())

    def __eq__(self, other):
        if isinstance(other, ForeignKeyConstraint):
            return (
                self.name == other.name
                and self.violation_error_message == other.violation_error_message
                and self.fields == other.fields
                and self.to_model == other.to_model
                and self.to_fields == other.to_fields
                and self.deferrable == other.deferrable
            )
        return super().__eq__(other)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["to_model"] = self.to_model
        kwargs["fields"] = self.fields
        kwargs["to_fields"] = self.to_fields
        kwargs["deferrable"] = self.deferrable
        return path, args, kwargs


class RawSQL(BaseConstraint):
    def __init__(self, *, name, sql, reverse_sql):
        super().__init__(name)
        self.sql = sql
        self.reverse_sql = reverse_sql

    def create_sql(self, model, schema_editor):
        return self.sql

    def remove_sql(self, model, schema_editor):
        return self.reverse_sql

    def constraint_sql(self, model, schema_editor):
        return None

    def validate(self, *args, **kwargs):
        return True

    def __eq__(self, other):
        if isinstance(other, RawSQL):
            return (
                self.name == other.name
                and self.sql == other.sql
                and self.reverse_sql == other.reverse_sql
            )
        return super().__eq__(other)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["sql"] = self.sql
        kwargs["reverse_sql"] = self.reverse_sql
        return path, args, kwargs


class View(BaseConstraint):
    def __init__(self, *, name, query, is_materialized=False):
        super().__init__(name)
        if isinstance(query, str):
            self.query = query
        elif isinstance(query, QuerySet):
            self.query = self.render_query(query.query)
        else:
            raise TypeError("string or Query expected")
        self.is_materialized = is_materialized

    def render_query(self, query):
        sql, params = query.sql_with_params()
        with connection.cursor() as cursor:
            return cursor.mogrify(sql, params).decode("utf-8")

    def create_sql(self, model, schema_editor):
        if self.is_materialized:
            remove_sql = self.remove_sql(model, schema_editor)
            return f"{remove_sql}; CREATE MATERIALIZED VIEW {self.name} AS {self.query}"

        return f"CREATE OR REPLACE VIEW {self.name} AS {self.query}"

    def remove_sql(self, model, schema_editor):
        qualifier = "MATERIALIZED" if self.is_materialized else ""
        return f"DROP {qualifier} VIEW IF EXISTS {self.name} CASCADE"

    def constraint_sql(self, model, schema_editor):
        return None

    def validate(self, *args, **kwargs):
        return True

    def __eq__(self, other):
        if isinstance(other, View):
            return (
                self.name == other.name
                and self.query == other.query
                and self.is_materialized == other.is_materialized
            )
        return super().__eq__(other)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["query"] = self.query
        kwargs["is_materialized"] = self.is_materialized
        return path, args, kwargs


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

    def constraint_sql(self, model, schema_editor):
        return None

    def validate(self, *args, **kwargs):
        return True

    def __eq__(self, other):
        if isinstance(other, Callback):
            return (
                self.name == other.name
                and self.callback == other.callback
                and self.reverse_callback == other.reverse_callback
            )

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["callback"] = self.callback
        kwargs["reverse_callback"] = self.reverse_callback
        return path, args, kwargs
