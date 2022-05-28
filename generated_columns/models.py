import sys

from django.db import models


class GeneratedColumnMixin:

    # This adds the field to the RETURNING clause of an INSERT. UPDATE is not supported.
    db_returning = True

    def __init__(self, *args, expression=None, **kwargs):
        if not expression:
            raise ValueError("expression required")
        self.expression = expression
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        # Extend the database type declaration with the GENERATED clause
        return f"{super().db_type(connection)} GENERATED ALWAYS AS ({self.expression}) STORED"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["expression"] = self.expression
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, private_only=False):
        # XXX #1
        # Setting private_only=True has the effect of excluding the field with inserts/updates and including with fetches
        # however breaks migration autodetector + migrate.

        # XXX #2
        # Don't set private_only=True when autodetection or migrate are run.
        # Conveniently we don't have to resort to checking sys.argv for migrate as the models with be the "fake"
        # migration state models.

        if "makemigrations" not in sys.argv and cls.__module__ != "__fake__":
            private_only = True

        super().contribute_to_class(cls, name, private_only=private_only)

        # XXX alternative
        # Overriding concrete is also a possibility can prevents inserts/updates and works with migrations,
        # but it also has the effect of removing the field from any fetches... a workaround may be to use
        # annotate() but noting that you can't annotate onto an existing field model.

        # self.concrete = False


class GeneratedIntegerField(GeneratedColumnMixin, models.IntegerField):
    ...


class Squared(models.Model):
    operand = models.IntegerField()
    result = GeneratedIntegerField(expression="operand * operand")

    def __str__(self):
        return f"{self.operand} * {self.operand} == {self.result}"


#
# Demonstrate something more practical: Enforcing user emails from a table-managed domain whitelist
#


class DomainForeignKey(GeneratedColumnMixin, models.ForeignKey):
    def get_attname_column(self):
        return self.get_attname(), self.name


class DomainWhitelist(models.Model):
    domain = models.CharField(primary_key=True, max_length=254)

    def __str__(self):
        return self.domain


class Person(models.Model):
    email = models.EmailField(unique=True)
    email_domain = DomainForeignKey(
        DomainWhitelist,
        expression="substring(email from '@(.*)$')",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.email
