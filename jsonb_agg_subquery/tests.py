import pytest
from django.db.models import OuterRef

from .models import JSONBAggSubquery, Pizza, Topping

pytestmark = pytest.mark.django_db


def test_jsonb_agg_subquery():
    pineapple = Pizza.objects.create(name="Pineapple Pizza")
    Topping.objects.create(pizza=pineapple, name="Tomato paste")
    Topping.objects.create(pizza=pineapple, name="Cheese")
    Topping.objects.create(pizza=pineapple, name="Ham")
    Topping.objects.create(pizza=pineapple, name="Pineapple")

    pizzas = Pizza.objects.values(
        "name",
        toppings=JSONBAggSubquery(
            Topping.objects.filter(pizza=OuterRef("pk")).values("name")
        ),
    )

    assert list(pizzas) == [
        {
            "name": "Pineapple Pizza",
            "toppings": [
                {"name": "Tomato paste"},
                {"name": "Cheese"},
                {"name": "Ham"},
                {"name": "Pineapple"},
            ],
        }
    ]


def test_jsonb_agg_subquery_with_model_type():
    pineapple = Pizza.objects.create(name="Pineapple Pizza")
    tomato_paste = Topping.objects.create(pizza=pineapple, name="Tomato paste")
    cheese = Topping.objects.create(pizza=pineapple, name="Cheese")
    ham = Topping.objects.create(pizza=pineapple, name="Ham")
    pineapple = Topping.objects.create(pizza=pineapple, name="Pineapple")

    pizzas = Pizza.objects.values(
        "name",
        toppings=JSONBAggSubquery(
            Topping.objects.filter(pizza=OuterRef("pk")), model=Topping
        ),
    )

    assert list(pizzas) == [
        {
            "name": "Pineapple Pizza",
            "toppings": [tomato_paste, cheese, ham, pineapple],
        }
    ]
