from datetime import date, datetime, time

import pytest
from django.db.models import F

from .models import Foo

pytestmark = pytest.mark.django_db


def test_combine():
    Foo.objects.create(foo=date(2025, 1, 1), bar=time(12))

    res = Foo.objects.annotate(timestamp=F("foo") + F("bar")).values_list(
        "timestamp", flat=True
    )

    assert list(res) == [datetime(2025, 1, 1, 12)]
