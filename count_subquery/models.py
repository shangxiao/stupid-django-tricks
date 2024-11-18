from django.db import models


class CountSubquery(models.Subquery):
    def __init__(self, queryset, **kwargs):
        super().__init__(
            queryset.values(_=models.Func("pk", function="COUNT")),
            **kwargs,
        )


class Author(models.Model):
    name = models.CharField()


class Publication(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField()
