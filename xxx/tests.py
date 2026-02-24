from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db.models import F

from xxx.models import Event, Location, EventNote

pytestmark = pytest.mark.django_db


def test_get():
    Event.objects.create(
        location=Location.objects.create(location="New York", timezone="America/New_York"),
        event_date="2026-01-01",
        start_time="09:00",
        end_time="10:00",
    )

    event = Event.objects.annotate(diff=F("end_timestamp") - F("start_timestamp")).get()

    assert event.start_timestamp == datetime(2026, 1, 1, 9, tzinfo=ZoneInfo("America/New_York"))
    assert event.end_timestamp == datetime(2026, 1, 1, 10, tzinfo=ZoneInfo("America/New_York"))
    assert event.diff == timedelta(hours=1)


def test_update():
    Event.objects.create(
        location=Location.objects.create(location="New York", timezone="America/New_York"),
        event_date="2026-01-01",
        start_time="09:00",
        end_time="10:00",
    )

    Event.objects.filter(end_time="10:00").update(end_time="11:00")

    event = Event.objects.get()
    assert event.start_timestamp == datetime(2026, 1, 1, 9, tzinfo=ZoneInfo("America/New_York"))


def test_refresh_from_db():
    event = Event.objects.create(
        location=Location.objects.create(location="New York", timezone="America/New_York"),
        event_date="2026-01-01",
        start_time="09:00",
        end_time="10:00",
    )

    event.refresh_from_db(from_queryset=Event.objects.all())

    assert event.start_timestamp == datetime(2026, 1, 1, 9, tzinfo=ZoneInfo("America/New_York"))
    assert event.end_timestamp == datetime(2026, 1, 1, 10, tzinfo=ZoneInfo("America/New_York"))


def test_deferred_attribute():
    event = Event.objects.create(
        location=Location.objects.create(location="New York", timezone="America/New_York"),
        event_date="2026-01-01",
        start_time="09:00",
        end_time="10:00",
    )

    assert event.start_timestamp == datetime(2026, 1, 1, 9, tzinfo=ZoneInfo("America/New_York"))
    assert event.end_timestamp == datetime(2026, 1, 1, 10, tzinfo=ZoneInfo("America/New_York"))


def test_validation():
    event = Event.objects.create(
        location=Location.objects.create(location="New York", timezone="America/New_York"),
        event_date="2026-01-01",
        start_time="09:00",
        end_time="10:00",
    )
    event.refresh_from_db()

    event.validate_constraints()


def test_related():
    event = Event.objects.create(
        location=Location.objects.create(location="New York", timezone="America/New_York"),
        event_date="2026-01-01",
        start_time="09:00",
        end_time="10:00",
    )
    EventNote.objects.create(event=event, note="oh hai")

    breakpoint()
    note = EventNote.objects.select_related("event").get()
    # assert note.event.start_timestamp == datetime(2026, 1, 1, 9, tzinfo=ZoneInfo("America/New_York"))
