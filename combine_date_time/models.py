from django.db import models
from django.db.models.expressions import Combinable, register_combinable_fields

register_combinable_fields(
    models.DateField,
    Combinable.ADD,
    models.TimeField,
    models.DateTimeField,
)


class Foo(models.Model):
    foo = models.DateField()
    bar = models.TimeField()
