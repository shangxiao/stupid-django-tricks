from django.db import models


class GroupsByRestaurant(models.Model):
    name = models.CharField(max_length=255)
    employee = models.CharField(max_length=255)
    restaurant = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.employee} - {self.restaurant}"


# This doesn't work as Django wraps filter arguments with parens which is invalid syntax
class AllSubquery(models.Subquery):
    template = "ALL (%(subquery)s)"


@models.Field.register_lookup
class AllSubqueryLookup(models.Lookup):
    lookup_name = "all"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = list(lhs_params) + list(rhs_params)
        return "%s = ALL %s" % (lhs, rhs), params
