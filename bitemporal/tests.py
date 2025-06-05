from datetime import datetime, timedelta, timezone

import pytest

from bitemporal.models import Account

pytestmark = pytest.mark.django_db(databases=["bitemporal"])


def test_valid_time_default():
    now = datetime.now(timezone.utc)

    alice = Account.objects.using("bitemporal").create(
        name="Alice", address="Melbourne"
    )

    # no way to mock pg's now()? for now assert close enough
    assert (now - alice.valid_time.lower) <= timedelta(minutes=1)
    assert alice.valid_time.upper == datetime.max  # simulates infinity


def test_update():
    alice = Account.objects.using("bitemporal").create(
        name="Alice", address="Melbourne"
    )
    alice.address = "Sydney"

    alice.save()

    history = Account.objects.using("bitemporal").all()
    assert len(history) == 2
