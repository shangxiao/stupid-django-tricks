import pytest
from django.db.models import sql

from .models import Product, mogrify_queryset

pytestmark = pytest.mark.django_db


def UpdateQueryWith(**kwargs):
    class UpdateQuery(sql.UpdateQuery):
        def _setup_query(self):
            super()._setup_query()
            self.add_update_values(kwargs)

    return UpdateQuery


def test_delete():
    print()
    print()
    print(mogrify_queryset(Product.objects.filter(name="Foo"), sql.DeleteQuery))
    print()


def test_update():
    print()
    print()
    print(
        mogrify_queryset(
            Product.objects.filter(name="Foo"), UpdateQueryWith(name="Bar")
        )
    )
    print()


def test_delete_query():
    print()
    print()
    print(Product.objects.filter(name="Foo").delete_query())
    print()


def test_update_query():
    print()
    print()
    print(Product.objects.filter(name="Foo").update_query(name="Bar"))
    print()
