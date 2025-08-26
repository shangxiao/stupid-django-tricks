import contextlib

import pytest
from django.db import connection, transaction


# First attempt: manually revert the value at the end of the context block. Manually wrap in a tx to help mitigate
# leakage?
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


# Wrap in tx if not in tx & set, otherwise check if it's not set already. Error if already set.
# This is still not ideal because it falsely encourages the idea that exiting the context will somehow reset the value?
@contextlib.contextmanager
def set_config_2(param, value):
    if not connection.in_atomic_block:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("select set_config(%s, %s, true)", [param, str(value)])
            yield
    else:
        with connection.cursor() as cursor:
            cursor.execute("select current_setting(%s, true)", [param])
            curr_value = cursor.fetchone()[0]
            if curr_value == str(value):
                yield
            elif curr_value is None or curr_value == "":
                cursor.execute("select set_config(%s, %s, true)", [param, str(value)])
                yield
            else:
                raise RuntimeError("Cannot set config within another config")


# maybe the only safe thing is to have a regular function that asserts within tx and only then sets the config.
# There's no false pretenses about operating in/out of block.
def set_config_3(param, value):
    if not connection.in_atomic_block:
        raise RuntimeError("Must be within atomic")

    with connection.cursor() as cursor:
        if value is None or value == "":
            cursor.execute("select set_config(%s, '', true)", [param])
            return

        cursor.execute("select current_setting(%s, true)", [param])
        curr_value = cursor.fetchone()[0]
        if curr_value == str(value):
            return
        elif curr_value is None or curr_value == "":
            cursor.execute("select set_config(%s, %s, true)", [param, str(value)])
        else:
            raise RuntimeError("Cannot change config within another config")


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


@pytest.mark.django_db(transaction=True)
def test_set_config_2():
    with set_config_2("app.user", 32):
        with connection.cursor() as cursor:
            cursor.execute("select current_setting('app.user', true)::int")
            assert cursor.fetchone()[0] == 32

    with connection.cursor() as cursor:
        cursor.execute("select current_setting('app.user', true)")
        assert cursor.fetchone()[0] == ""


@pytest.mark.django_db(transaction=True)
def test_set_config_2_within_tx():
    with transaction.atomic():
        with set_config_2("app.user", 32):  # should this just be an error instead?
            with connection.cursor() as cursor:
                cursor.execute("select current_setting('app.user', true)::int")
                assert cursor.fetchone()[0] == 32


@pytest.mark.django_db(transaction=True)
def test_set_config_2_double_set_same_value_is_ok():
    with set_config_2("app.user", 32):
        with set_config_2("app.user", 32):
            pass


@pytest.mark.django_db(transaction=True)
def test_set_config_2_double_set_different_value_is_error():
    with set_config_2("app.user", 32):
        with pytest.raises(RuntimeError):
            with set_config_2("app.user", 64):
                pass


@pytest.mark.django_db(transaction=True)
def test_set_config_3_no_tx_error():
    with pytest.raises(RuntimeError):
        set_config_3("app.user", 35)


@pytest.mark.django_db(transaction=True)
def test_set_config_3_in_tx():
    with transaction.atomic():
        set_config_3("app.user", 35)
        with connection.cursor() as cursor:
            cursor.execute("select current_setting('app.user', true)::int")
            assert cursor.fetchone()[0] == 35

        # allow clearing
        set_config_3("app.user", None)

        with connection.cursor() as cursor:
            cursor.execute("select current_setting('app.user', true)")
            assert cursor.fetchone()[0] == ""

        set_config_3("app.user", 35)

        # ignore if same value
        set_config_3("app.user", 35)

        # setting different value is an error
        with pytest.raises(RuntimeError):
            set_config_3("app.user", 36)

    with connection.cursor() as cursor:
        cursor.execute("select current_setting('app.user', true)")
        assert cursor.fetchone()[0] == ""
