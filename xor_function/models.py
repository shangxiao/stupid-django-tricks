from django.db import models
from django.db.models.expressions import Func
from django.db.models.functions import Cast


class Xor(Func):
    template = "(%(expressions)s) = 1"
    arg_joiner = " + "
    output_field = models.BooleanField()

    def __init__(self, *expressions, output_field=None, **extra):
        updated_expressions = []
        for e in expressions:
            updated_expression = Cast(e, models.IntegerField())
            updated_expression.empty_result_set_value = 0
            updated_expressions.append(updated_expression)

        super().__init__(*updated_expressions, output_field=output_field, **extra)


class User(models.Model):
    is_standard_user_type = models.BooleanField(default=False)
    is_staff_user_type = models.BooleanField(default=False)
    is_admin_user_type = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="only_one_type",
                check=Xor(
                    models.F("is_standard_user_type"),
                    models.F("is_staff_user_type"),
                    models.F("is_admin_user_type"),
                ),
            )
        ]


class Foo(models.Model):
    ...


class Bar(models.Model):
    ...


class Baz(models.Model):
    foo = models.ForeignKey(Foo, null=True, on_delete=models.CASCADE)
    bar = models.ForeignKey(Bar, null=True, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="only_one_fk",
                check=Xor(
                    ~models.Q(foo=None),
                    ~models.Q(bar=None),
                ),
            )
        ]
