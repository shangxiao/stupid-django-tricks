import pytest
from django.db.models import CharField, F
from django.db.models.aggregates import Sum

from .models import Data, OrderByNoGroup, RefNoGroup, Rollup

pytestmark = pytest.mark.django_db


def test_grouping_sets():
    Data.objects.create(category_1="Foo", category_2="Fizz", data=2)
    Data.objects.create(category_1="Foo", category_2="Buzz", data=3)
    Data.objects.create(category_1="Bar", category_2="Fizz", data=5)
    Data.objects.create(category_1="Bar", category_2="Buzz", data=1)

    qs = (
        Data.objects.annotate(
            data_sum=Sum("data"),
        )
        .values(
            "data_sum",
            rollup=Rollup("category_1", "category_2"),
        )
        .values(
            "data_sum",
            cat_1=RefNoGroup("category_1", output_field=CharField()),
            cat_2=RefNoGroup("category_2", output_field=CharField()),
        )
        .order_by(
            OrderByNoGroup(F("category_1"), nulls_first=True),
            OrderByNoGroup(F("category_2"), nulls_first=True),
        )
    )

    assert list(qs.all()) == [
        {
            "cat_1": None,
            "cat_2": None,
            "data_sum": 11,
        },
        {
            "cat_1": "Bar",
            "cat_2": None,
            "data_sum": 6,
        },
        {
            "cat_1": "Bar",
            "cat_2": "Buzz",
            "data_sum": 1,
        },
        {
            "cat_1": "Bar",
            "cat_2": "Fizz",
            "data_sum": 5,
        },
        {
            "cat_1": "Foo",
            "cat_2": None,
            "data_sum": 5,
        },
        {
            "cat_1": "Foo",
            "cat_2": "Buzz",
            "data_sum": 3,
        },
        {
            "cat_1": "Foo",
            "cat_2": "Fizz",
            "data_sum": 2,
        },
    ]
