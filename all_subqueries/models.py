from django.core.exceptions import EmptyResultSet
from django.db import models
from django.db.models import fields
from django.db.models.lookups import (
    Exact,
    GreaterThan,
    GreaterThanOrEqual,
    LessThan,
    LessThanOrEqual,
)


class GroupsByRestaurant(models.Model):
    name = models.CharField(max_length=255)
    employee = models.CharField(max_length=255)
    restaurant = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.employee} - {self.restaurant}"


class Employee(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Score(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.employee}'s score of {self.score}"


# This doesn't work as Django wraps filter arguments with parens which is invalid syntax
class AllSubquery(models.Subquery):
    template = "ALL (%(subquery)s)"


class AllMixin:
    def get_rhs_op(self, connection, rhs):
        return connection.operators[super().lookup_name] % f"ALL {rhs}"


@models.Field.register_lookup
class AllLookup(AllMixin, Exact):
    lookup_name = "all"


@models.Field.register_lookup
class ExactAll(AllMixin, Exact):
    lookup_name = "exact_all"


@models.Field.register_lookup
class GreaterThanAll(AllMixin, GreaterThan):
    lookup_name = "gt_all"


@models.Field.register_lookup
class GreaterThanOrEqualAll(AllMixin, GreaterThanOrEqual):
    lookup_name = "gte_all"


@models.Field.register_lookup
class LessThanlAll(AllMixin, LessThan):
    lookup_name = "lt_all"


@models.Field.register_lookup
class LessThanOrEqualAll(AllMixin, LessThanOrEqual):
    lookup_name = "lte_all"


class All(models.Subquery):
    # Identical to models.Exists with the line `query = self.query.exists(...)` removed!
    template = "'t' = ALL (%(subquery)s)"
    output_field = fields.BooleanField()

    def __init__(self, queryset, negated=False, **kwargs):
        self.negated = negated
        super().__init__(queryset, **kwargs)

    def __invert__(self):
        clone = self.copy()
        clone.negated = not self.negated
        return clone

    def as_sql(self, compiler, connection, template=None, **extra_context):
        try:
            sql, params = super().as_sql(
                compiler,
                connection,
                template=template,
                **extra_context,
            )
        except EmptyResultSet:
            if self.negated:
                features = compiler.connection.features
                if not features.supports_boolean_expr_in_select_clause:
                    return "1=1", ()
                return compiler.compile(models.Value(True))
            raise
        if self.negated:
            sql = "NOT {}".format(sql)
        return sql, params

    def select_format(self, compiler, sql, params):
        # Wrap EXISTS() with a CASE WHEN expression if a database backend
        # (e.g. Oracle) doesn't support boolean expression in SELECT or GROUP
        # BY list.
        if not compiler.connection.features.supports_boolean_expr_in_select_clause:
            sql = "CASE WHEN {} THEN 1 ELSE 0 END".format(sql)
        return sql, params


class AllWorkaround(models.Exists):
    def __init__(self, queryset, correlating_filters=None, **kwargs):
        where_node = queryset.query.where.clone()
        where_node.negated = not where_node.negated
        queryset.query.where.children = [where_node]
        if correlating_filters:
            queryset = queryset.filter(correlating_filters)
        super().__init__(queryset, negated=True, **kwargs)
