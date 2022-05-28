import pytest

from .models import Squared

pytestmark = pytest.mark.django_db


def test_create_and_returning():
    """
    Ensure that a create operation will not attempt to insert into the generated column yet includes the
    field in the RETURNING clause.
    """
    assert Squared.objects.create(operand=2).result == 4


def test_fetch():
    """
    Ensure that we can still retrieve the column's value with a fetch.
    """
    Squared.objects.create(operand=2)

    assert Squared.objects.get(operand=2).result == 4


def test_update():
    """
    Ensure that a model save will not attempt to update the generated column.
    """
    s = Squared.objects.create(operand=2)
    s.operand = 3
    s.result = 5

    s.save()

    s.refresh_from_db()
    assert s.result == 9
