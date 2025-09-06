YesNo Database Function
=======================

September 2025


Like the [`yesno` template filter](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/#yesno) that converts a
boolean into "yes" or "no", we can define a custom Django `Func` which does the same thing but on the DB layer.

In this case the function does not use a database function per se but a case expression, we just need to repeat the
`%(expression)s` placeholder for each when clause. We just need to take care to repeat the params for as many times as
the expression placeholder is declared in the template.

We can override the initialiser to accept labels for yes & no with the defaults of "Yes" and "No" respectively.


```python
class YesNo(Func):
    template = "CASE WHEN %(expressions)s = TRUE THEN '%(yes)s' WHEN %(expressions)s = FALSE THEN '%(no)s' ELSE '' END"
    output_field = CharField()
    arity = 1

    def __init__(self, expression, yes="Yes", no="No", **extra):
        super().__init__(expression, **extra | {"yes": yes, "no": no})

    def as_sql(self, *args, **kwargs):
        sql, params = super().as_sql(*args, **kwargs)
        return sql, params + params
```
