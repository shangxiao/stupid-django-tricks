import pytest

from .models import Foo, YesNo

pytestmark = pytest.mark.django_db


def test_yesno():
    Foo.objects.create()

    assert list(
        Foo.objects.values(
            yes=YesNo(True),
            no=YesNo(False),
            active=YesNo(True, yes="Active", no="Inactive"),
            inactive=YesNo(False, yes="Active", no="Inactive"),
        )
    ) == [
        {
            "yes": "Yes",
            "no": "No",
            "active": "Active",
            "inactive": "Inactive",
        }
    ]
