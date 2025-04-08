from datetime import date, datetime, timedelta, timezone

import pytest
from django.db.models import Exists, OuterRef

from .models import (
    BetterGenerateIntegerSeries,
    GenerateDateSeries,
    GenerateDateTimeSeries,
    GenerateIntegerSeries,
)

pytestmark = pytest.mark.django_db


def test_integer_series():
    """
    Test basic integer series
    """
    int_series = GenerateIntegerSeries.objects.all(start=2, stop=10, interval=2)

    assert len(int_series) == 5
    assert [obj.series for obj in int_series] == [2, 4, 6, 8, 10]


def test_date_series():
    """
    Test basic date series generation
    """
    date_series = GenerateDateSeries.objects.all(
        start=date(2020, 1, 1),
        stop=date(2020, 1, 31),
        interval=timedelta(days=1),
    )

    assert len(date_series) == 31
    assert date_series[0].date == date(2020, 1, 1)
    assert date_series[1].date == date(2020, 1, 2)
    assert date_series[29].date == date(2020, 1, 30)
    assert date_series[30].date == date(2020, 1, 31)


def test_datetime_series():
    """
    Test datetime series generation complete with timezone
    """
    utc = timezone.utc
    datetime_series = GenerateDateTimeSeries.objects.all(
        start=datetime(2020, 1, 1, 9, 0, 0, tzinfo=utc),
        stop=datetime(2020, 1, 1, 16, 0, 0, tzinfo=utc),
        interval=timedelta(hours=1),
    )

    assert len(datetime_series) == 8
    assert datetime_series[0].timestamptz == datetime(2020, 1, 1, 9, 0, 0, tzinfo=utc)
    assert datetime_series[1].timestamptz == datetime(2020, 1, 1, 10, 0, 0, tzinfo=utc)
    assert datetime_series[6].timestamptz == datetime(2020, 1, 1, 15, 0, 0, tzinfo=utc)
    assert datetime_series[7].timestamptz == datetime(2020, 1, 1, 16, 0, 0, tzinfo=utc)


def test_better_integer_series():
    int_series = BetterGenerateIntegerSeries.objects.params(
        start=2, stop=10, interval=2
    ).all()

    assert [obj.series for obj in int_series] == [2, 4, 6, 8, 10]


def test_as_subquery():
    int_series = (
        BetterGenerateIntegerSeries.objects.params(start=1, stop=10, interval=1)
        .all()
        .filter(
            Exists(
                BetterGenerateIntegerSeries.objects.params(
                    start=2, stop=4, interval=1
                ).filter(series=OuterRef("series"))
            )
        )
    )

    assert [obj.series for obj in int_series] == [2, 3, 4]
