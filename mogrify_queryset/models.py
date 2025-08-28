from django.core.exceptions import EmptyResultSet
from django.db import connection, models
from django.db.models import sql
from django.db.models.sql.where import WhereNode


def mogrify_queryset(qs, query_class=None):
    query = qs.query
    if query_class:
        query = query.chain(query_class)
    with connection.cursor() as cur:
        try:
            return cur.mogrify(*query.sql_with_params())

        except EmptyResultSet:
            # An EmptyResultSet means a filter was declared that's a logical contradiction
            # (ie that will never be true), for eg foo__in=[]
            #
            # We still need a query with a compatible select clause; in order to do
            # that we can clear the where clause and add "limit 0"
            # It's not ideal as it doesn't show the originally requested where clause
            # (ie if required for debugging purposes) but it functions equivalently
            # if required to execute by itself or interpolated in a larger query.

            query = query.clone()
            query.where = WhereNode()
            return cur.mogrify(*query.sql_with_params()) + " LIMIT 0"


def UpdateQueryWith(**kwargs):
    class UpdateQuery(sql.UpdateQuery):
        def _setup_query(self):
            super()._setup_query()
            self.add_update_values(kwargs)

    return UpdateQuery


class Product(models.Model):
    name = models.CharField()
