from datetime import date, datetime

from django.db import models
from django.db.models.expressions import BaseExpression, Ref
from django.db.models.lookups import Exact
from django.db.models.sql.constants import LOUTER


class SeriesRef(Ref):
    def __init__(self, alias=None, output_field=None):
        self.alias = alias
        self.output_field = output_field

    def as_sql(self, compiler, connection):
        return connection.ops.quote_name(self.alias), []

    def get_source_expressions(self):
        return []

    def get_refs(self):
        return {}

    def __repr__(self):
        # override Ref.__repr__ to avoid printing refs & source
        return "{}({})".format(self.__class__.__name__, self.alias)


class GenerateSeriesJoin:
    join_type = LOUTER  # required? does this keep join chaining outer?
    filtered_relation = None
    nullable = False

    def __init__(self, start, stop, step, join_clause, alias, parent_alias):
        self.start = start
        self.stop = stop
        self.step = step
        self.join_clause = join_clause
        self.table_name = alias
        self.table_alias = alias
        self.parent_alias = parent_alias

    def as_sql(self, compiler, connection):
        params = [self.start, self.stop, self.step]
        join_clause, join_params = self.join_clause.as_sql(compiler, connection)
        alias = connection.ops.quote_name(self.table_alias)
        return (
            f"RIGHT OUTER JOIN generate_series(%s, %s, %s) {alias} ON ({join_clause})",
            params + join_params,
        )


class GenerateSeriesConditionalExpression(BaseExpression):
    """
    This class hooks into expression resolution by pretending to be a conditional expression.
    """

    conditional = True
    output_field = models.BooleanField()

    def __init__(self, *, start, stop, step, join_condition, alias="series"):
        self.start = start
        self.stop = stop
        self.step = step
        self.join_condition = join_condition
        self.alias = alias

        # bother to check that start, stop & step are all consistent types?

        if isinstance(self.start, datetime):
            self.output_field = models.DateTimeField()
        elif isinstance(self.start, date):
            self.output_field = models.DateField()
        else:
            self.output_field = models.IntegerField()

        for expr in self.join_condition.flatten():
            if isinstance(expr, SeriesRef):
                expr.output_field = self.output_field
                expr.alias = self.alias

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        query.join(
            GenerateSeriesJoin(
                start=self.start,
                stop=self.stop,
                step=self.step,
                join_clause=self.join_condition.resolve_expression(query),
                alias=self.alias,
                parent_alias=query.get_initial_alias(),
            )
        )
        query.add_annotation(
            SeriesRef(alias=self.alias, output_field=self.output_field),
            self.alias,
        )
        return Exact(True, True)


class GenerateSeries(SeriesRef):
    """
    Overload SeriesRef so that we can additionally hook into expression resolution and setup our custom join.
    """

    def __init__(self, *, start, stop, step, join_condition, alias="series"):
        self.start = start
        self.stop = stop
        self.step = step
        self.join_condition = join_condition
        self.alias = alias
        # default_alias is what Django uses to determine the aggregations added to annotate()
        self.default_alias = alias

        # bother to check that start, stop & step are all consistent types?

        if isinstance(self.start, datetime):
            self.output_field = models.DateTimeField()
        elif isinstance(self.start, date):
            self.output_field = models.DateField()
        else:
            self.output_field = models.IntegerField()

        for expr in self.join_condition.flatten():
            if isinstance(expr, SeriesRef):
                expr.output_field = self.output_field
                expr.alias = self.alias

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        query.join(
            GenerateSeriesJoin(
                start=self.start,
                stop=self.stop,
                step=self.step,
                join_clause=self.join_condition.resolve_expression(query),
                alias=self.alias,
                parent_alias=query.get_initial_alias(),
            )
        )
        return self


class LinkedData(models.Model):
    data = models.IntegerField()


class Data(models.Model):
    timestamp = models.DateTimeField()
    data = models.IntegerField(null=True)
    linked_data = models.ForeignKey(
        LinkedData, on_delete=models.CASCADE, null=True, related_name="+"
    )
