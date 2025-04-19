from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import connections, models
from django.db.models.expressions import Ref
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.query import Query
from django.utils.hashable import make_hashable

# TODO: complain if group by is not explicitly set when encountering an aggregating expression??


# Group by:
#  - Query.group_by attribute
#    - set to True when aggregation is annotated
#    - otherwise Query.set_group_by() will set this to a combination of values_select and annotation_select
#  - SQLCompiler.get_group_by()
#    - Uses a combination of items from Query.group_by, select & order_by
#    - resolves any field name references
#    - optionally collapses group by cols into the minimal functional dependency (eg pk)
#    - changes expressions into ordinal notation where can (if can)
#    - compiles exprsesions into sql


class MyCompiler(SQLCompiler):
    # def collapse_group_by(self, expressions, having):
    #     expressions = super().collapse_group_by(expressions, having)
    #     # remove any unnecessary cols that other expressions are referencing??
    #     exprs_to_remove = []
    #     for expr in expressions:
    #         if isinstance(expr, Col):
    #             for other_expr in expressions:
    #                 if (
    #                     other_expr is not expr
    #                     and expr in other_expr.get_source_expressions()
    #                 ):
    #                     exprs_to_remove += [expr]
    #                     continue
    #     return [e for e in expressions if e not in exprs_to_remove]

    def get_group_by(self, select, order_by):
        # use legacy group by if not set
        if self.query._group_by == set():
            return super().get_group_by(select, order_by)

        # adapted from super().get_group_by()
        # but with the auto select, order, etc fetching *removed*
        # and query.group_by references replaced with query._group_by

        expressions = []
        group_by_refs = set()
        for expr in self.query._group_by:
            if not hasattr(expr, "as_sql"):
                expr = self.query.resolve_ref(expr)
            if isinstance(expr, Ref):
                if expr.refs not in group_by_refs:
                    group_by_refs.add(expr.refs)
                    expressions.append(expr.source)
            else:
                expressions.append(expr)

        selected_expr_positions = {}
        for ordinal, (expr, _, alias) in enumerate(select, start=1):
            if alias:
                selected_expr_positions[expr] = ordinal

        result = []
        seen = set()
        expressions = self.collapse_group_by(expressions, having=[])

        allows_group_by_select_index = (
            self.connection.features.allows_group_by_select_index
        )
        for expr in expressions:
            try:
                sql, params = self.compile(expr)
            except (EmptyResultSet, FullResultSet):
                continue
            if (
                allows_group_by_select_index
                and (position := selected_expr_positions.get(expr)) is not None
            ):
                sql, params = str(position), ()
            else:
                sql, params = expr.select_format(self, sql, params)
            params_hash = make_hashable(params)
            if (sql, params_hash) not in seen:
                result.append((sql, params))
                seen.add((sql, params_hash))
        return result

        # do nothing except use the query's group by
        return [self.compile(expr.get_group_by_cols()) for expr in self.query._group_by]


class MyQuery(Query):
    # manual_group_by = False
    _group_by = None
    is_group_by_required = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._group_by = set()  # can't do at class level

    def get_compiler(self, using=None, connection=None, elide_empty=True):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        # note the switched order
        return MyCompiler(self, connection, using, elide_empty)

    # @property
    # def group_by(self):
    #     if self._group_by:
    #         return self._group_by
    #     else:
    #         return super().group_by

    # @group_by.setter
    # def group_by(self, value):
    #     super().group_by = value
    #     # if value is True:
    #     #     self.is_group_by_required = True
    #     # pass

    # def set_group_by(self, allow_aliases=True):
    #     pass
    #     # breakpoint()
    #     # if not self.manual_group_by:
    #     #     super().set_group_by(allow_aliases)

    def chain(self, klass=None):
        obj = super().chain(klass)
        obj._group_by = self._group_by
        # obj.manual_group_by = self.manual_group_by
        obj.is_group_by_required = self.is_group_by_required
        return obj

    def as_sql(self, *args, **kwargs):
        if self.is_group_by_required:
            pass  # potentially do a sanity check here?  or just let it do a programming error

        return super().as_sql(*args, **kwargs)


class BaseQuerySet(models.QuerySet):
    def __init__(self, model=None, query=None, *args, **kwargs):
        _query = query or MyQuery(model)
        super().__init__(model, _query)

    def group_by(self, *fields_or_expressions):
        clone = self._chain()
        # clone.query.manual_group_by = True
        # if not fields and not expressions:
        if not fields_or_expressions:
            clone.query._group_by = set()
        else:
            clone.query._group_by |= {
                (
                    field.resolve_expression(clone.query)
                    if hasattr(field, "resolve_expression")
                    else field
                )
                for field in fields_or_expressions
            }

        return clone


class Store(models.Model):
    location = models.CharField()


class Product(models.Model):
    objects = BaseQuerySet.as_manager()

    name = models.CharField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
