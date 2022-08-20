import pytest
from django.db.models import Exists, OuterRef, Q, Subquery, Value

from .models import All, Employee, GroupsByRestaurant, Score

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

    # Verify with equivalent NOT EXISTS (inverted subquery) expression
    not_exists_qs = (
        GroupsByRestaurant.objects.filter(
            ~Exists(subquery.filter(name=OuterRef("name")).exclude(restaurant="KFC"))
        )
        .values("name")
        .distinct()
    )
    assert list(not_exists_qs) == list(only_groups_where_all_members_are_from_kfc)


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


def test_all_true():
    bob = Employee.objects.create(name="Bob")
    Score.objects.create(employee=bob, score=5)
    Score.objects.create(employee=bob, score=10)
    joe = Employee.objects.create(name="Joe")
    Score.objects.create(employee=joe, score=10)
    Score.objects.create(employee=joe, score=15)

    top_scoring = Employee.objects.filter(
        All(
            Score.objects.filter(employee=OuterRef("id"))
            .annotate(score_gte_10=Q(score__gte=10))
            .values("score_gte_10")
        )
    )

    assert len(top_scoring) == 1
    assert top_scoring[0].name == "Joe"

    # Verify negation
    not_top_scoring = Employee.objects.filter(
        ~All(
            Score.objects.filter(employee=OuterRef("id"))
            .annotate(score_gte_10=Q(score__gte=10))
            .values("score_gte_10")
        )
    )
    assert len(not_top_scoring) == 1
    assert not_top_scoring[0].name == "Bob"
