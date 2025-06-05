from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresqlDatabaseWrapper,
)
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgresqlDatabaseSchemaEditor,
)


class DatabaseSchemaEditor(PostgresqlDatabaseSchemaEditor):
    # no point to override here because it requires varying injection
    # def quote_name(self, name):
    #     return self.connection.ops.quote_name(name)

    def _pk_constraint_sql(self, columns):
        return (
            self.sql_pk_constraint
            % {
                "columns": ", ".join(
                    (
                        f"{self.quote_name(column)} WITHOUT OVERLAPS"
                        if column == "valid_time"
                        else self.quote_name(column)
                    )
                    for column in columns
                )
            }
            # Can't do this with PKs that will be referred to:
            # "cannot use a deferrable unique constraint for referenced table "bitemporal_account""
            # + " DEFERRABLE INITIALLY DEFERRED"
        )


class DatabaseWrapper(PostgresqlDatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
