from django.db import models
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
class All(AllMixin, Exact):
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
