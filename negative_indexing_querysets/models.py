from django.db import models


class LevelQuerySet(models.QuerySet):
    def __getitem__(self, key):
        if isinstance(key, int) and key < 0:
            if self.ordered:
                queryset = self.reverse()
            else:
                self._check_ordering_first_last_queryset_aggregation(method="last")
                queryset = self.order_by("-pk")
            key = abs(key) - 1
            return queryset[key]
        else:
            return super().__getitem__(key)


class Level(models.Model):
    objects = LevelQuerySet.as_manager()

    name = models.CharField()
    order = models.IntegerField()
