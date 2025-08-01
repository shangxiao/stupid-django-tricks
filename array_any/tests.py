import pytest
from django.db.models import Q

from .models import Product

pytestmark = pytest.mark.django_db


def test_array_any():
    first = Product.objects.create(name="First", options=["foo", "bar"])
    Product.objects.create(name="Second", options=["baz"])

    assert set(Product.objects.filter(options__any="bar")) == {first}


def test_not():
    Product.objects.create(name="First", options=["foo", "bar"])
    second = Product.objects.create(name="Second", options=["baz"])

    assert set(Product.objects.filter(~Q(options__any="bar"))) == {second}
