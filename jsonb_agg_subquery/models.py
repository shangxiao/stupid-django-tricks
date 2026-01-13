from django.db import models


class Pizza(models.Model):
    name = models.CharField()


class Topping(models.Model):
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    name = models.CharField()


class ModelJSONField(models.JSONField):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        return [self.model(**v) for v in value]


class JSONBAggSubquery(models.Subquery):
    template = "(SELECT jsonb_agg(t) FROM (%(subquery)s) t)"
    output_field = models.JSONField()

    def __init__(self, queryset, model=None, output_field=None, **extra):
        if model:
            output_field = ModelJSONField(model)
        super().__init__(queryset, output_field, **extra)
