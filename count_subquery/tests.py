import pytest
from django.db import models

from .models import Author, CountSubquery, Publication

pytestmark = pytest.mark.django_db


def test_count_as_subquery():
    fred = Author.objects.create(name="Fred")
    Publication.objects.create(title="A Tale of Two Cities", author=fred)
    Publication.objects.create(title="For Whom the Bell Tolls", author=fred)

    qs = Author.objects.annotate(
        num_books=CountSubquery(
            Publication.objects.filter(author=models.OuterRef("pk"))
        )
    )

    assert list(qs.values_list("num_books", flat=True)) == [2]


def test_count_no_rows():
    Author.objects.create(name="Fred")

    qs = Author.objects.annotate(
        num_books=CountSubquery(
            Publication.objects.filter(author=models.OuterRef("pk"))
        )
    )

    assert list(qs.values_list("num_books", flat=True)) == [0]
