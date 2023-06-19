from datetime import datetime, timedelta, timezone

import pytest
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import (
    Data,
    GenerateSeries,
    GenerateSeriesConditionalExpression,
    LinkedData,
    SeriesRef,
)

pytestmark = pytest.mark.django_db

utc = timezone.utc


def test_generate_series_as_filter():
    one = LinkedData.objects.create(data=1)
    Data.objects.create(timestamp=datetime(2000, 1, 1, 12, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 1, 13, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 2, 12, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 3, 12, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 3, 13, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 3, 14, tzinfo=utc), linked_data=one)

    series = GenerateSeriesConditionalExpression(
        start=datetime(2000, 1, 1, tzinfo=utc),
        stop=datetime(2000, 1, 5, tzinfo=utc),
        step=timedelta(days=1),
        join_condition=Q(
            timestamp__gte=SeriesRef(),
            timestamp__lte=SeriesRef() + Value(timedelta(days=1)),
        ),
    )
    dataset = (
        Data.objects.filter(series)
        .values("series")
        .annotate(sum=Coalesce(Sum("linked_data__data"), 0))
        .values("series", "sum")
        .order_by("series")
    )

    assert list(dataset) == [
        {
            "series": datetime(2000, 1, 1, tzinfo=utc),
            "sum": 2,
        },
        {
            "series": datetime(2000, 1, 2, tzinfo=utc),
            "sum": 1,
        },
        {
            "series": datetime(2000, 1, 3, tzinfo=utc),
            "sum": 3,
        },
        {
            "series": datetime(2000, 1, 4, tzinfo=utc),
            "sum": 0,
        },
        {
            "series": datetime(2000, 1, 5, tzinfo=utc),
            "sum": 0,
        },
    ]


def test_generate_series_as_annotation():
    one = LinkedData.objects.create(data=1)
    Data.objects.create(timestamp=datetime(2000, 1, 1, 12, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 1, 13, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 2, 12, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 3, 12, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 3, 13, tzinfo=utc), linked_data=one)
    Data.objects.create(timestamp=datetime(2000, 1, 3, 14, tzinfo=utc), linked_data=one)

    series = GenerateSeries(
        start=datetime(2000, 1, 1, tzinfo=utc),
        stop=datetime(2000, 1, 5, tzinfo=utc),
        step=timedelta(days=1),
        join_condition=Q(
            timestamp__gte=SeriesRef(),
            timestamp__lte=SeriesRef() + Value(timedelta(days=1)),
        ),
        alias="series",
    )
    dataset = (
        Data.objects.annotate(series)
        .values("series")
        .annotate(sum=Coalesce(Sum("linked_data__data"), 0))
        .values("series", "sum")
        .order_by("series")
    )

    assert list(dataset) == [
        {
            "series": datetime(2000, 1, 1, tzinfo=utc),
            "sum": 2,
        },
        {
            "series": datetime(2000, 1, 2, tzinfo=utc),
            "sum": 1,
        },
        {
            "series": datetime(2000, 1, 3, tzinfo=utc),
            "sum": 3,
        },
        {
            "series": datetime(2000, 1, 4, tzinfo=utc),
            "sum": 0,
        },
        {
            "series": datetime(2000, 1, 5, tzinfo=utc),
            "sum": 0,
        },
    ]
