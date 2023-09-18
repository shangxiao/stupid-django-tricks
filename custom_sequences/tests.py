import pytest

from .models import ModelWithMultipleSequenceFields

pytestmark = pytest.mark.django_db


def test_sequence():
    model = ModelWithMultipleSequenceFields.objects.create()
    assert model.sequence_1 == 1
    assert model.sequence_2 == 10

    model_2 = ModelWithMultipleSequenceFields.objects.create()
    assert model_2.sequence_1 == 2
    assert model_2.sequence_2 == 15
