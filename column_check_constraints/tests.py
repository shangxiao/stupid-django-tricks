import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from column_check_constraints.models import Project

pytestmark = pytest.mark.django_db


def test_percentage():
    project = Project.objects.create(percentage=50)
    project.validate_constraints()

    invalid_project = Project(percentage=-1)

    with pytest.raises(ValidationError):
        invalid_project.validate_constraints()

    with pytest.raises(IntegrityError):
        invalid_project.save()
