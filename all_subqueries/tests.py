import pytest
from django.db.models import OuterRef, Subquery, Value

from .models import Employee, GroupsByRestaurant, Score

pytestmark = pytest.mark.django_db


def test_all_subquery():
    GroupsByRestaurant.objects.create(
        name="People from both KFC and Gami Chicken",
        employee="Joe",
        restaurant="Gami Chicken",
    )
    GroupsByRestaurant.objects.create(
        name="People from both KFC and Gami Chicken",
        employee="Bob",
        restaurant="KFC",
    )
    GroupsByRestaurant.objects.create(
        name="Only KFC",
        employee="Bob",
        restaurant="KFC",
    )
    GroupsByRestaurant.objects.create(
        name="Only KFC",
        employee="Alice",
        restaurant="KFC",
    )
    subquery = GroupsByRestaurant.objects.filter(name=OuterRef("name")).values(
        "restaurant"
    )
    only_groups_where_all_members_are_from_kfc = (
        GroupsByRestaurant.objects.annotate(only_kfc=Value("KFC"))
        .filter(only_kfc__all=Subquery(subquery))
        .values("name")
        .distinct()
    )

    assert len(only_groups_where_all_members_are_from_kfc) == 1
    assert only_groups_where_all_members_are_from_kfc[0]["name"] == "Only KFC"


def test_different_operator():
    bob = Employee.objects.create(name="Bob")
    Score.objects.create(employee=bob, score=5)
    Score.objects.create(employee=bob, score=10)
    joe = Employee.objects.create(name="Joe")
    Score.objects.create(employee=joe, score=10)
    Score.objects.create(employee=joe, score=15)

    top_scoring = Employee.objects.annotate(threshold=Value(10)).filter(
        threshold__lte_all=Subquery(
            Score.objects.filter(employee=OuterRef("id")).values("score")
        )
    )

    assert len(top_scoring) == 1
    assert top_scoring[0].name == "Joe"
