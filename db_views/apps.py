import collections.abc

import django.db.backends.postgresql.schema as postgresql_schema
from django.apps import AppConfig
from django.conf import settings
from django.core.management.commands import makemigrations, migrate
from django.db.migrations import state
from django.db.migrations.operations.base import Operation
from django.db.migrations.serializer import (
    BaseSerializer,
    Serializer,
    serializer_factory,
)
from django.db.models import QuerySet, options
from django.db.utils import load_backend

# from django.db.models.options import DEFAULT_NAMES

# proposal on Django GitHub
# DEFAULT_NAMES.update(["db_view", "query", "materialized"])

if "db_view" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = tuple(options.DEFAULT_NAMES) + ("db_view",)
if "query" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = tuple(options.DEFAULT_NAMES) + ("query",)
if "materialized" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = tuple(options.DEFAULT_NAMES) + ("materialized",)


class UpdateView(Operation):
    def __init__(self, model_name, db_view, query, materialized, *args, **kwargs):
        self.model_name = model_name
        self.db_view = db_view
        self.query = query
        self.materialized = materialized
        super().__init__(*args, **kwargs)

    def state_forwards(self, app_label, state):
        model_state = state.models[app_label, self.model_name]
        model_state.options["db_view"] = self.db_view
        model_state.options["query"] = self.query
        model_state.options["materialized"] = self.materialized
        state.reload_model(app_label, self.model_name, delay=True)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from_model = from_state.apps.get_model(app_label, self.model_name)
        to_model = to_state.apps.get_model(app_label, self.model_name)

        # Materialized views need to be dropped, they cannot be simply replaced.
        # Also when changing a view to materialized, pg seems to silently ignore the query?
        # but requires dropping to change anyway.
        if from_model._meta.materialized or to_model._meta.materialized:
            schema_editor.delete_view(from_model)

        schema_editor.create_view(to_model)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # the backwards operations are the same
        self.database_forwards(app_label, schema_editor, from_state, to_state)


class MigrationAutodetectorMixin:
    def _detect_changes(self, *args, **kwargs):
        # we can't hook into migration generation before or after _detect_changes(), will need to hook into one of the steps
        # taking place within this method
        return super()._detect_changes(*args, **kwargs)

    def create_altered_constraints(self):
        self.check_altered_view_defs()
        return super().create_altered_constraints()

    def check_altered_view_defs(self):
        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]
            old_db_view = old_model_state.options.get("db_view", False)
            new_db_view = new_model_state.options.get("db_view", False)

            if old_db_view != new_db_view:
                raise Exception(
                    "Cannot change a model to/from a view unless removed first"
                )

            from mogrify_queryset.models import mogrify_queryset

            old_query = old_model_state.options.get("query")
            if isinstance(old_query, QuerySet):
                old_query = mogrify_queryset(old_query)
            new_query = new_model_state.options.get("query")
            if isinstance(new_query, QuerySet):
                new_query = mogrify_queryset(new_query)
            old_materialized = old_model_state.options.get("materialized")
            new_materialized = new_model_state.options.get("materialized")

            if old_query != new_query or old_materialized != new_materialized:
                self.add_operation(
                    app_label,
                    UpdateView(
                        model_name=model_name,
                        db_view=new_db_view,
                        query=new_query,
                        materialized=new_materialized,
                    ),
                )


def patch_migrations():
    if "triggers" not in state.DEFAULT_NAMES:
        state.DEFAULT_NAMES = tuple(state.DEFAULT_NAMES) + ("db_view",)
    if "query" not in state.DEFAULT_NAMES:
        state.DEFAULT_NAMES = tuple(state.DEFAULT_NAMES) + ("query",)
    if "materialized" not in state.DEFAULT_NAMES:
        state.DEFAULT_NAMES = tuple(state.DEFAULT_NAMES) + ("materialized",)

    if not issubclass(makemigrations.MigrationAutodetector, MigrationAutodetectorMixin):
        makemigrations.MigrationAutodetector = type(
            "MigrationAutodetector",
            (
                MigrationAutodetectorMixin,
                makemigrations.MigrationAutodetector,
            ),
            {},
        )

    if not issubclass(migrate.MigrationAutodetector, MigrationAutodetectorMixin):
        migrate.MigrationAutodetector = type(
            "MigrationAutodetector",
            (MigrationAutodetectorMixin, migrate.MigrationAutodetector),
            {},
        )

    makemigrations.Command.autodetector = makemigrations.MigrationAutodetector
    migrate.Command.autodetector = makemigrations.MigrationAutodetector


class DatabaseSchemaEditorMixin:
    def create_model(self, model):
        if getattr(model._meta, "db_view", False):
            return self.create_view(model)
        return super().create_model(model)

    def delete_model(self, model):
        if getattr(model._meta, "db_view", False):
            return self.delete_view(model)
        return super().delete_model(model)

    def create_view(self, model):
        table = self.quote_name(model._meta.db_table)
        query = model._meta.query
        materialized = model._meta.materialized
        sql = (
            f"CREATE OR REPLACE VIEW {table} AS {query}"
            if not materialized
            else f"CREATE MATERIALIZED VIEW IF NOT EXISTS {table} AS {query}"
        )
        self.execute(sql, [])

    def delete_view(self, model):
        table = self.quote_name(model._meta.db_table)
        materialized = model._meta.materialized
        sql = (
            f"DROP VIEW IF EXISTS {table}"
            if not materialized
            else f"DROP MATERIALIZED VIEW IF EXISTS {table}"
        )
        self.execute(sql, [])


def patch_schema_editor():
    for config in settings.DATABASES.values():
        backend = load_backend(config["ENGINE"])
        schema_editor_class = backend.DatabaseWrapper.SchemaEditorClass

        if (
            schema_editor_class
            and issubclass(
                schema_editor_class,
                postgresql_schema.DatabaseSchemaEditor,
            )
            and not issubclass(schema_editor_class, DatabaseSchemaEditorMixin)
        ):
            backend.DatabaseWrapper.SchemaEditorClass = type(
                "DatabaseSchemaEditor",
                (DatabaseSchemaEditorMixin, schema_editor_class),
                {},
            )


class QuerySetSerializer(BaseSerializer):
    def serialize(self):
        from mogrify_queryset.models import mogrify_queryset

        value, _ = serializer_factory(mogrify_queryset(self.value)).serialize()

        return value, []


class DbViewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "db_views"

    def ready(self):

        patch_migrations()
        patch_schema_editor()

        # unregister() should return the serializer
        iterable_serializer = Serializer._registry.pop(collections.abc.Iterable)
        Serializer.register(QuerySet, QuerySetSerializer)
        Serializer.register(collections.abc.Iterable, iterable_serializer)
