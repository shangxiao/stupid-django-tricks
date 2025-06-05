from functools import cached_property
from django.db.backends.ddl_references import Columns, Statement, Table

from django.contrib.postgres.fields.ranges import DateTimeRangeField
from django.db import models
from django.db.models.constraints import Deferrable
from django.db.models.expressions import RawSQL

from abusing_constraints.constraints import ForeignKeyConstraint
from abusing_constraints.constraints import RawSQL as RawSQLConstraint

#
# Todo:
#
# ✓ btree_gist extension installed
#   - manually inject into migrations
#   - from django.contrib.postgres.operations import BtreeGistExtension
#     BtreeGistExtension(),
#
# ✓ Define PK
#   ✓ CompositePrimaryKey
#   ✓ WITHOUT OVERLAPS
#     - Overriding backend schema editor
#   ✗ must be deferrable initially deferred
#     - cannot do with PKs that have a FK reference
#
# - FK
#   - CompositeForeignKey
#     - not ready yet
#     ✓ workaround using constraint
#     - use this custom relationship thing from Kogan? https://devblog.kogan.com/blog/custom-relationships-in-django
#     ✓ define with PERIOD
#       - customise the workaround
#
# - PG<->Python adaptation of infinity
#   ✓ -> Python
#   ✓ <- Python
#
# - Triggers
#   - Replace save/delete with update
#     ✓ using a trigger defined by constraints hack
#     - better way to avoid recursion without resorting to pg_trigger_depth()?
#     - returned update/delete rows are always 0 - way to fix this?
#   - Force transaction with trigger?
#   - Read-only except for current valid time update
#     - using a trigger defined by constraints hack
#   - Batches to avoid n+1 ??
#
# - Should we be blocking the update of the natural key?
#
#
# - views?
#


# class DateTimeRangeConstructor(Func):
#    function = "tstzrange"


"""\
create or replace function account_update_function()
returns trigger as $$
begin

    raise notice 'here2 %', pg_trigger_depth();
    if pg_trigger_depth() < 2 then
        if upper(old.valid_time) = 'infinity' then
            raise notice 'here';
            update bitemporal_account
            set valid_time = tstzrange(lower(valid_time), now())
            where name = new.name and valid_time = new.valid_time;

            -- insert new entry with updated values
            insert into bitemporal_account (name, address) values (new.name, new.address);
        end if;

        return null;
    end if;

    return new;
end;
$$ language plpgsql;
"""


"""\
CREATE OR REPLACE FUNCTION account_delete_function()
RETURNS trigger AS $$
BEGIN
    IF upper(OLD.valid_time) = 'infinity' THEN
        -- Simply close out the last entry
        UPDATE bitemporal_account
        SET valid_time = tstzrange(lower(valid_time), now())
        WHERE name = OLD.name AND valid_time = OLD.valid_time;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""

"""\
CREATE TRIGGER account_delete_trigger
BEFORE DELETE ON bitemporal_account
FOR EACH ROW
EXECUTE FUNCTION account_delete_function();
"""


account_update_function = """\
CREATE OR REPLACE FUNCTION account_update_function()
RETURNS trigger AS $$
BEGIN
    -- Insert new entry with updated values
    INSERT INTO bitemporal_account (name, address) VALUES (NEW.name, NEW.address);

    -- Prevent the original update by using OLD with only updated valid_time
    OLD.valid_time := tstzrange(lower(OLD.valid_time), now());
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
"""

account_update_function_reverse = """\
# DROP FUNCTION IF EXISTS account_update_function;
"""

# INSTEAD OF UPDATE ON bitemporal_account only work on view
account_update_trigger = """\
CREATE TRIGGER account_update_trigger
BEFORE UPDATE ON bitemporal_account
FOR EACH ROW
EXECUTE FUNCTION account_update_function();
"""

account_update_trigger_reverse = """\
DROP TRIGGER IF EXISTS account_update_trigger ON bitemporal_account;
"""


# this is attempt 2 and doesn't work
#
# account_update_valid_time_function = """\
# CREATE OR REPLACE FUNCTION account_update_valid_time_function()
# RETURNS trigger AS $$
# BEGIN
#     -- Prevent the original update by using OLD with only updated valid_time
#     OLD.valid_time := tstzrange(lower(OLD.valid_time), now());
#     RETURN OLD;
# END;
# $$ LANGUAGE plpgsql;
# """
#
# account_update_valid_time_function_reverse = """\
# DROP FUNCTION IF EXISTS account_update_valid_time_function;
# """
#
# account_update_insert_new_values_function = """\
# CREATE OR REPLACE FUNCTION account_update_insert_new_values_function()
# RETURNS trigger AS $$
# BEGIN
#     -- Insert new entry with updated values
#     INSERT INTO bitemporal_account (name, address) VALUES (NEW.name, NEW.address);
#
#     RETURN NULL;
# END;
# $$ LANGUAGE plpgsql;
# """
#
# account_update_insert_new_values_function_reverse = """\
# DROP FUNCTION IF EXISTS account_update_insert_new_values_function;
# """
#
# account_update_valid_time_trigger = """\
# CREATE TRIGGER account_update_valid_time_trigger
# BEFORE UPDATE ON bitemporal_account
# FOR EACH ROW
# EXECUTE FUNCTION account_update_valid_time_function();
# """
#
# account_update_valid_time_trigger_reverse = """\
# DROP TRIGGER IF EXISTS account_update_valid_time_trigger ON bitemporal_account;
# """
#
# account_update_insert_new_values_trigger = """\
# CREATE TRIGGER account_update_insert_new_values_trigger
# AFTER UPDATE ON bitemporal_account
# FOR EACH ROW
# EXECUTE FUNCTION account_update_insert_new_values_function();
# """
#
# account_update_insert_new_values_trigger_reverse = """\
# DROP TRIGGER IF EXISTS account_update_insert_new_values_trigger ON bitemporal_account;
# """


class ValidTimeCompositePrimaryKey(models.CompositePrimaryKey):
    @cached_property
    def columns(self):
        return tuple(
            (
                f"{field.column} WITHOUT OVERLAPS"
                if field.column == "valid_time"
                else field.column
            )
            for field in self.fields
        )


class TemporalColumns(Columns):
    def __str__(self):
        def col_str(column, idx):
            col = self.quote_name(column)
            try:
                suffix = self.col_suffixes[idx]
                if suffix:
                    col = "{} {}".format(col, suffix)
            except IndexError:
                pass
            return col

        return ", ".join(
            (
                f"PERIOD {col_str(column, idx)}"
                if column == "valid_time"
                else col_str(column, idx)
            )
            for idx, column in enumerate(self.columns)
        )


class TemporalForeignKeyConstraint(ForeignKeyConstraint):
    def create_sql(self, model, schema_editor, sql_create_fk=None):
        sql = sql_create_fk or schema_editor.sql_create_fk
        table = Table(model._meta.db_table, schema_editor.quote_name)
        name = schema_editor.quote_name(self.name)
        column_names = [
            model._meta.get_field(field_name).get_attname()
            for field_name in self.fields
        ]
        columns = TemporalColumns(table, column_names, schema_editor.quote_name)
        to_model = self.get_to_model(model)
        to_table = Table(to_model._meta.db_table, schema_editor.quote_name)
        to_column_names = [
            to_model._meta.get_field(field_name).get_attname()
            for field_name in self.to_fields
        ]
        to_columns = TemporalColumns(
            to_table, to_column_names, schema_editor.quote_name
        )
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


class Account(models.Model):
    pk = models.CompositePrimaryKey("name", "valid_time")
    name = models.CharField()
    # valid time should have a DB default from edit time til placeholder for "now"
    # but since there's no placeholder then we'll have to use infinity; this is probably
    # ok but just means we can't store future dates?
    valid_time = DateTimeRangeField(
        db_default=RawSQL("tstzrange(now(), 'infinity', '[)')", params=[]),
        # db_default=RawSQL("tstzrange(now(), 'infinity', '[]')", params=[]),
        # DateTimeRangeField(Now(), Value("infinity"), Value("[]"))
    )
    address = models.CharField()

    class Meta:
        constraints = [
            RawSQLConstraint(
                name="account_update_function",
                sql=account_update_function,
                reverse_sql=account_update_function_reverse,
            ),
            RawSQLConstraint(
                name="account_update_trigger",
                sql=account_update_trigger,
                reverse_sql=account_update_trigger_reverse,
            ),
        ]


class Shift(models.Model):
    account_name = models.CharField()
    valid_time = DateTimeRangeField()
    # this is unnecessary
    # valid_time_upper = models.GeneratedField(
    #     expression=Func(
    #         Func(models.F("valid_time"), function="upper"),
    #         Func(models.F("valid_time"), function="upper"),
    #         models.Value("[]"),
    #         function="tstzrange",
    #     ),
    #     db_persist=True,
    #     output_field=DateTimeRangeField(),
    # )
    # composite FKs aren't ready yet
    # account = models.ForeignKey(
    #     Account,
    #     from_fields=("account_name", "valid_time_upper"),
    #     to_fields=("name", "valid_time"),
    #     on_delete=models.DO_NOTHING,
    # )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="fuck",
                fields=["account_name"],
            ),
            TemporalForeignKeyConstraint(
                name="shift_account_temporal_fk",
                fields=("account_name", "valid_time"),
                to_model=Account,
                to_fields=("name", "valid_time"),
                # temporal FKs *must* be deferrable initially deferred
                deferrable=Deferrable.DEFERRED,
            ),
        ]
