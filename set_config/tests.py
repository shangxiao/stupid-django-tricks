import contextlib

import pytest
from django.db import connection, transaction


@contextlib.contextmanager
def set_config(param, value):
    # Start transaction & set local as a bit of an extra safeguard. Even when used after a savepoint, an error will
    # also rollback the parameter (but not upon success however).
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("select current_setting('app.user', true)")
            prior_value = cursor.fetchone()[0]

            cursor.execute("select set_config(%s, %s, true)", [param, str(value)])

            def get_config():
                cursor.execute("select current_setting(%s, true)", [param])
                return type(value)(cursor.fetchone()[0])

            yield get_config

            cursor.execute(
                "select set_config(%s, %s, true)",
                [param, "" if prior_value is None else str(prior_value)],
            )


@pytest.mark.django_db(transaction=True)
def test_set_config():
    with set_config("app.user", 12) as config:
        with connection.cursor() as cursor:
            cursor.execute("select current_setting('app.user', true)::int")
            assert cursor.fetchone()[0] == 12
            assert config() == 12

            with set_config("app.user", 13) as config:
                assert config() == 13

            cursor.execute("select current_setting('app.user', true)::int")
            assert cursor.fetchone()[0] == 12

    with connection.cursor() as cursor:
        cursor.execute("select current_setting('app.user', true)")
        assert cursor.fetchone()[0] == ""


@pytest.mark.django_db
def test_set_config_as_tx():
    with set_config("app.user", 12) as config:
        assert config() == 12

    with connection.cursor() as cursor:
        cursor.execute("select current_setting('app.user', true)")
        assert cursor.fetchone()[0] == ""
