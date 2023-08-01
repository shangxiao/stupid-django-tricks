import itertools

from django.db import models
from django.db.models.expressions import RawSQL, Subquery, Window
from django.db.models.functions import RowNumber
from django.db.models.query import QuerySet
from django.db.models.sql.constants import LOUTER


class SubqueryJoin(Subquery):
    # just used to satisfy Query? eg existing_inner in build_filter()
    # but could still be useful?
    join_type = LOUTER
    table_name = "t"


class PatchedQuerySet(QuerySet):
    alias_name = "t"

    def __mul__(self, other):
        class AnonymousModel(models.Model):
            objects = PatchedQuerySet.as_manager()

        queryset = PatchedQuerySet(AnonymousModel)
        # explicitly set the required pk to just a row number
        # if doing a values() without fields id will still be added though
        queryset.query.default_cols = False
        queryset.query.add_annotation(Window(RowNumber()), "id")

        alias, _ = queryset.query.table_alias(self.alias_name, create=True)
        self_subquery = SubqueryJoin(self)
        self_subquery.template = f"{Subquery.template} {alias}"
        self_subquery.resolve_expression(query=queryset.query)
        queryset.query.alias_map[alias] = self_subquery

        for field in itertools.chain(
            self.query.values_select, self.query.annotations.keys()
        ):
            model_name = self.model._meta.model_name
            new_field_name = model_name + "_" + field
            queryset.query.add_annotation(
                RawSQL(sql=alias + "." + field, params=[]), new_field_name
            )

        other_alias, _ = queryset.query.table_alias(self.alias_name, create=True)
        other_subquery = SubqueryJoin(other)
        other_subquery.template = f", {Subquery.template} {other_alias}"
        other_subquery.resolve_expression(query=queryset.query)
        queryset.query.alias_map[other_alias] = other_subquery

        for field in itertools.chain(
            other.query.values_select, other.query.annotations.keys()
        ):
            new_field_name = other.model._meta.model_name + "_" + field
            queryset.query.add_annotation(
                RawSQL(sql=other_alias + "." + field, params=[]), new_field_name
            )

        return queryset


class Shop(models.Model):
    objects = PatchedQuerySet.as_manager()
    name = models.CharField()


class Product(models.Model):
    name = models.CharField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
