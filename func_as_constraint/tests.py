import pytest

from .models import HelloWorld, PlaceholderModel

pytestmark = pytest.mark.django_db


def test_hello_world():
    PlaceholderModel.objects.create()

    qs = PlaceholderModel.objects.annotate(hello_world=HelloWorld())

    assert qs[0].hello_world == "Hello World!"
