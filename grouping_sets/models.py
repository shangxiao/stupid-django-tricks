from django.db import models
from django.db.models.expressions import Expression, OrderBy, Ref


class RefNoGroup(Ref):
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

    def get_group_by_cols(self):
        return []


class OrderByNoGroup(OrderBy):
    def get_group_by_cols(self):
        return []


class RollupGroupBy(Expression):
    output_field = models.BooleanField()

    def __init__(self, *fields):
        self.fields = fields

    def as_sql(self, compiler, connection):
        fields = ", ".join([connection.ops.quote_name(field) for field in self.fields])
        return [
            f"ROLLUP ({fields})",
            [],
        ]


class Rollup(Expression):
    output_field = models.BooleanField()

    def __init__(self, *fields):
        self.fields = fields

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        # XXX: override the attempt to group by all values
        # Note that we can't add any annotations to query here as this expression will be used with values() and the
        # mask will be in the process of being reset.
        query.group_by = [RollupGroupBy(*self.fields)]

        return self


class Data(models.Model):
    category_1 = models.CharField()
    category_2 = models.CharField()
    data = models.IntegerField()
