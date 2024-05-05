import pytest

from .models import User

pytestmark = pytest.mark.django_db


def test_formset_get(client):
    response = client.get("/bulk_create_form/")

    assert response.status_code == 200
    assert response.context["formset"].management_form["TOTAL_FORMS"].value() == 1
    assert response.context["formset"].management_form["MIN_NUM_FORMS"].value() == 1


def test_formset_post__min_required__1_form(client):
    response = client.post(
        "/bulk_create_form/",
        data={
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 1,
            "form-MAX_NUM_FORMS": 1000,
            "form-0-name": "",
            "form-0-email": "",
        },
    )

    assert response.status_code == 200
    assert not response.context["formset"].is_valid()
    assert response.context["formset"].errors == [
        {
            "name": ["This field is required."],
            "email": ["This field is required."],
        }
    ]


def test_formset_post__min_required__5_forms(client):
    response = client.post(
        "/bulk_create_form/",
        data={
            "form-TOTAL_FORMS": 5,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 1,
            "form-MAX_NUM_FORMS": 1000,
            "form-0-name": "",
            "form-0-email": "",
        },
    )

    assert response.status_code == 200
    assert not response.context["formset"].is_valid()
    assert response.context["formset"].errors == [
        {
            "name": ["This field is required."],
            "email": ["This field is required."],
        },
        {},
        {},
        {},
        {},
    ]


def test_formset_post__invalid_email(client):
    response = client.post(
        "/bulk_create_form/",
        data={
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 1,
            "form-MAX_NUM_FORMS": 1000,
            "form-0-name": "invalid",
            "form-0-email": "invalid",
            "form-1-name": "valid",
            "form-1-email": "valid@valid.com",
        },
    )

    assert response.status_code == 200
    assert not response.context["formset"].is_valid()
    assert response.context["formset"].errors == [
        {
            "email": ["Enter a valid email address."],
        },
        {},
    ]


def test_formset_post__duplicate_email(client):
    User.objects.create(name="duplicate", email="duplicate@duplicate.com")

    response = client.post(
        "/bulk_create_form/",
        data={
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 1,
            "form-MAX_NUM_FORMS": 1000,
            "form-0-name": "duplicate",
            "form-0-email": "duplicate@duplicate.com",
            "form-1-name": "valid",
            "form-1-email": "valid@valid.com",
        },
    )

    assert response.status_code == 200
    assert not response.context["formset"].is_valid()
    assert response.context["formset"].errors == [
        {
            "email": ["User with this Email already exists."],
        },
        {},
    ]


def test_formset_post__valid(client):
    response = client.post(
        "/bulk_create_form/",
        data={
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 1,
            "form-MAX_NUM_FORMS": 1000,
            "form-0-name": "valid_1",
            "form-0-email": "valid_1@valid.com",
            "form-1-name": "valid_2",
            "form-1-email": "valid_2@valid.com",
        },
    )

    assert response.status_code == 200
    assert list(User.objects.values("name", "email").order_by("name")) == [
        {
            "name": "valid_1",
            "email": "valid_1@valid.com",
        },
        {
            "name": "valid_2",
            "email": "valid_2@valid.com",
        },
    ]
