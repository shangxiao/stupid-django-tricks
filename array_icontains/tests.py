import pytest

from .models import Product

pytestmark = pytest.mark.django_db


def test_array_icontains():
    first = Product.objects.create(name="First", options=["foo", "Bar", "BAZ"])
    second = Product.objects.create(name="Second", options=["Foo", "Bar", "baZ"])

    assert set(Product.objects.filter(options__icontains="Bar")) == {first, second}
