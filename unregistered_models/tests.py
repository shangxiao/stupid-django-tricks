import pytest
from django.db import models

pytestmark = pytest.mark.django_db


def test_unregistered_model():
    class Series(models.Model):
        # A primary key is still necessary; either declare one or return a field
        # called 'id'
        generate_series = models.CharField(primary_key=True)

    raw_queryset = Series.objects.raw("select generate_series(1, 10)")

    assert [item.generate_series for item in raw_queryset] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
    ]


def test_extraneous_fields():
    class SimpleModel(models.Model):
        ...

    raw_queryset = SimpleModel.objects.raw("select 1 as id, 'Hello' as greeting")

    assert [(item.id, item.greeting) for item in raw_queryset] == [(1, "Hello")]
