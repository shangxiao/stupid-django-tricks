import json

import pytest

from .models import Data

pytestmark = pytest.mark.django_db


def test_count_estimate():
    Data.objects.bulk_create(Data(value=i) for i in range(100_000))

    print(json.loads(Data.objects.all().explain(format="json"))[0]["Plan"]["Plan Rows"])
