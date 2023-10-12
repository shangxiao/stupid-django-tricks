import pytest
from django.db.models import F

from .models import Foo

pytestmark = pytest.mark.django_db


def test_annotation_overwrite():
    Foo.objects.create(foo=1)
    qs = Foo.objects.all()

    with pytest.raises(ValueError):
        # Fails with "The annotation 'foo' conflicts with a field on the model."
        qs.annotate(foo=F("foo") + 1)

    qs.query.add_annotation(F("foo") + 1, "foo")

    foo = qs.get()
    assert foo.foo == 2
