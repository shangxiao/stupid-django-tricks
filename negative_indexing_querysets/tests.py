import pytest

from .models import Level

pytestmark = pytest.mark.django_db


def test_level_order():
    Level.objects.create(order=0, name="Ground Floor")
    Level.objects.create(order=1, name="First Floor")
    Level.objects.create(order=2, name="Second Floor")
    Level.objects.create(order=3, name="Third Floor")
    Level.objects.create(order=4, name="Fourth Floor")
    Level.objects.create(order=5, name="Fifth Floor")

    second_last = Level.objects.order_by("order")[-2]

    assert second_last.name == "Fourth Floor"


def test_pk_order():
    Level.objects.create(order=5, name="Fifth Floor")
    Level.objects.create(order=4, name="Fourth Floor")
    Level.objects.create(order=3, name="Third Floor")
    Level.objects.create(order=2, name="Second Floor")
    Level.objects.create(order=1, name="First Floor")
    Level.objects.create(order=0, name="Ground Floor")

    second_last = Level.objects.all()[-2]

    assert second_last.name == "First Floor"
