from django.db import models
from django.db.models.lookups import Lookup
from django.contrib.postgres.fields import ArrayField


class Product(models.Model):
    name = models.CharField(max_length=255)
    options = ArrayField(base_field=models.CharField(max_length=255))

    def __str__(self):
        return self.name


@ArrayField.register_lookup
class ArrayIContains(Lookup):
    lookup_name = "icontains"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = rhs_params + lhs_params
        return "%s ILIKE ANY(%s)" % (rhs, lhs), params
