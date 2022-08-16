import pytest
from django.db.models import OuterRef, Subquery, Value

from .models import GroupsByRestaurant

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
