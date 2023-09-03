from django.db import models
from django.db.models.expressions import Subquery
from django.db.models.query import QuerySet
from django.db.models.sql.constants import INNER


class SubqueryJoin(Subquery):
    table_name = "t"
    alias = "t"

    # the following attributes are referenced in a few places though not actually useful
    # just used to satisfy Query? eg existing_inner in build_filter()
    # used in join promotion - when we get a Q() filter there'll be join promotion
    join_type = INNER  # LOUTER requires a demote() method
    parent_alias = "t"
    nullable = False

    def resolve_expression(self, query, *args, **kwargs):
        self.outer_query = query
        return super().resolve_expression(query, *args, **kwargs)

    def as_sql(self, compiler, connection, template=None, **kwargs):
        # dynamically update with the alias. The alias is not simply 't', as it
        # can be bumped during resolve_expression()
        # why doesn't the alias exist in alias_refcount? 🤔
        # alias, _ = self.outer_query.table_alias(self.table_name, create=False)
        alias_list = self.outer_query.table_map.get(self.table_name)
        alias = alias_list[0]
        template = template or self.template
        template += f" {alias}"
        return super().as_sql(compiler, connection, template, **kwargs)


def subqueryset(inner_queryset):
    # optionally accept a model class as an argument and use that

    # Declaring new models on the fly:
    #  - What app to associate it with?
    #  - field clones ok?
    #  - how to create without pk?
    #    -
    #  - like a "readonly" model, we don't need a pk
    #    - there's a bunch of other benefits/assumptions with thiskj

    # Declare a new model on the fly with all the fields from select & annotations.
    # This is more reliable than an empty model and either trying to fudge the meta
    # to remove the standard pk or adding a superfluous row_number().

    attrs = (
        {
            # the metaclass requires this to be set to something
            "__module__": inner_queryset.model.__module__,
            # we could set Meta.db_table here to the alias 't' but it may not be necessary
            # "Meta": type("Meta", tuple(), {"db_table": "t"}),
        }
        | {col.target.name: col.target.clone() for col in inner_queryset.query.select}
        | {
            alias: annotation.output_field.clone()
            for alias, annotation in inner_queryset.query.annotations.items()
        }
    )
    # XXX set the first to pk
    for key, attr in attrs.items():
        if isinstance(attr, models.Field):
            attr.primary_key = True
            break
    TempModel = type("TempModel", tuple([models.Model]), attrs)

    outer_queryset = QuerySet(TempModel)

    subquery = SubqueryJoin(inner_queryset)
    # resolve_expression() does:
    #  - bump alias prefixes
    #  - resolve OuterRef (not useful here)
    #  - resolve sub exps
    #  - what else?
    subquery = subquery.resolve_expression(query=outer_queryset.query)

    # this line replaces `from model` -> `from (subquery) alias`
    alias, _ = outer_queryset.query.table_alias(subquery.table_name, create=True)
    outer_queryset.query.alias_map[alias] = subquery

    return outer_queryset


class Shop(models.Model):
    name = models.CharField()


class Product(models.Model):
    name = models.CharField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)


class Sales(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    date = models.DateField()
    sales = models.IntegerField()
