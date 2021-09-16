import functools

from django.db import models


def _property(**kwargs):
    def decorator(func):
        func.__dict__.update(kwargs)

        class Property:
            def __get__(self, instance, owner=None):
                if instance:
                    return func(instance)
                return func

        return Property()

    return decorator


class Foo(models.Model):
    foo = models.JSONField()

    @_property(lookup_expr="foo__bar")
    def bar(self):
        return self.foo["bar"]
