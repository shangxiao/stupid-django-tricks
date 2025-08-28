import pytest
from django.db.models.sql import DeleteQuery

from .models import Product, UpdateQueryWith, mogrify_queryset

pytestmark = pytest.mark.django_db


def test_delete_query():
    assert (
        mogrify_queryset(Product.objects.filter(name="Foo"), DeleteQuery)
        == """\
DELETE FROM "mogrify_queryset_product" WHERE "mogrify_queryset_product"."name" = 'Foo'\
"""
    )


def test_update_query():
    assert (
        mogrify_queryset(
            Product.objects.filter(name="Foo"), UpdateQueryWith(name="Bar")
        )
        == """\
UPDATE "mogrify_queryset_product" SET "name" = 'Bar' WHERE "mogrify_queryset_product"."name" = 'Foo'\
"""
    )
