import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from .models import Bar, Baz, Foo, User

pytestmark = pytest.mark.django_db


def test_xor_can_set_single_fields():
    User.objects.create(is_standard_user_type=True).validate_constraints()
    User.objects.create(is_staff_user_type=True).validate_constraints()
    User.objects.create(is_admin_user_type=True).validate_constraints()


def test_xor_raises_error_on_even_number_set():
    with pytest.raises(IntegrityError):
        User.objects.create(is_staff_user_type=True, is_admin_user_type=True)


def test_xor_raises_error_on_even_number_set_validation():
    with pytest.raises(ValidationError):
        User(is_staff_user_type=True, is_admin_user_type=True).validate_constraints()


def test_xor_raises_error_on_odd_number_set():
    with pytest.raises(IntegrityError):
        User.objects.create(
            is_standard_user_type=True, is_staff_user_type=True, is_admin_user_type=True
        )


def test_xor_raises_error_on_odd_number_set_validation():
    with pytest.raises(ValidationError):
        User(
            is_standard_user_type=True, is_staff_user_type=True, is_admin_user_type=True
        ).validate_constraints()


def test_baz_validation():
    # This should test EmptyResultSet due to the negation: foo is not null xor bar is not null
    foo = Foo.objects.create()
    bar = Bar.objects.create()

    Baz.objects.create(foo=foo).validate_constraints()
    Baz.objects.create(bar=bar).validate_constraints()

    with pytest.raises(ValidationError):
        Baz(foo=foo, bar=bar).validate_constraints()
