from textwrap import dedent

import pytest
from django.db import connection
from django.db.models.signals import pre_migrate
from django.dispatch import receiver
from django.utils import timezone
from freezegun import freeze_time

from mock_now.models import Now

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="session", autouse=True)
def setup_mock_now():
    """
    Mock NOW() by adding own implemenation to the default "public" schema.
    """

    @receiver(pre_migrate, weak=False)
    def setup_mock_now_pre_migrate(
        sender, app_config, verbosity, interactive, **kwargs
    ):
        if sender.name == "mock_now":
            with connection.cursor() as cursor:
                # Some folks suggest to use a different schema like pg_temp or another user define one but that breaks Django migrations.
                # Change search_path to put pg_catalog last which causes user defined objects to be prioritised over system objects.
                cursor.execute('SET SESSION search_path = "$user",public,pg_catalog')
                # If 'my.var' is not yet set current_setting('my.var', true) will return NULL, however if RESET will return empty string so requires nullif()
                cursor.execute(dedent("""\
                    CREATE OR REPLACE FUNCTION public.now()
                    RETURNS timestamptz
                    LANGUAGE plpgsql
                    STABLE
                    AS $$
                        BEGIN
                            RETURN coalesce(nullif(current_setting('my.now', true), '')::timestamptz, pg_catalog.now());
                        END;
                    $$;
                """))


@pytest.fixture
def mock_now():
    def do_mock_now(timestamp):
        with connection.cursor() as cursor:
            cursor.execute(
                f'SET LOCAL "my.now" = \'{timestamp.strftime("%Y-%m-%d %H:%M:%S%z")}\''
            )

    yield do_mock_now

    with connection.cursor() as cursor:
        cursor.execute('RESET "my.now"')

    return do_mock_now


@freeze_time("2026-01-01 12:00:00+00")
def test_mock_now(mock_now):
    mock_now(timezone.now())

    assert Now.objects.get().now == timezone.now()


def test_not_mock_now():
    now = timezone.now()
    now_now = Now.objects.get().now
    difference = now_now - now

    assert difference.total_seconds() <= 1
