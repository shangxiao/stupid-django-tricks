from django.db import models


class YesNo(models.Func):
    template = "CASE WHEN %(expressions)s = TRUE THEN '%(yes)s' WHEN %(expressions)s = FALSE THEN '%(no)s' ELSE '' END"
    output_field = models.CharField()
    arity = 1

    def __init__(self, expression, yes="Yes", no="No", **extra):
        super().__init__(expression, **extra | {"yes": yes, "no": no})

    def as_sql(self, *args, **kwargs):
        sql, params = super().as_sql(*args, **kwargs)
        return sql, params + params


class Foo(models.Model):
    pass
