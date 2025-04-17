import pytest
from django.db.models import CharField, Count, F, Func, OrderBy, Value
from django.db.models.expressions import Case, When
from django.db.models.functions import Coalesce, Concat
from django.db.utils import ProgrammingError

from explicit_group_by.models import Product, Store

pytestmark = pytest.mark.django_db


@pytest.fixture
def products():
    main = Store.objects.create(location="Main st")
    high = Store.objects.create(location="High st")
    Product.objects.bulk_create(
        [
            Product(store=main, name="UltraComfort Memory Foam Mattress"),
            Product(store=main, name="UltraComfort Memory Foam Mattress"),
            Product(store=main, name="UltraComfort Memory Foam Mattress"),
            Product(store=main, name="ProSeries Wireless Earbuds"),
            Product(store=main, name="ProSeries Wireless Earbuds"),
            Product(store=main, name="Sleek Stainless Steel Coffee Maker"),
            Product(store=main, name="Eco-Friendly Bamboo Toothbrush Set"),
            Product(store=main, name="Eco-Friendly Bamboo Toothbrush Set"),
            Product(store=main, name="Eco-Friendly Bamboo Toothbrush Set"),
            Product(store=main, name="Eco-Friendly Bamboo Toothbrush Set"),
            Product(store=main, name="Eco-Friendly Bamboo Toothbrush Set"),
        ]
    )
    Product.objects.bulk_create(
        [
            Product(store=high, name="UltraComfort Memory Foam Mattress"),
            Product(store=high, name="ProSeries Wireless Earbuds"),
            Product(store=high, name="ProSeries Wireless Earbuds"),
            Product(store=high, name="ProSeries Wireless Earbuds"),
            Product(store=high, name="ProSeries Wireless Earbuds"),
            Product(store=high, name="ProSeries Wireless Earbuds"),
            Product(store=high, name="Sleek Stainless Steel Coffee Maker"),
            Product(store=high, name="Sleek Stainless Steel Coffee Maker"),
            Product(store=high, name="Sleek Stainless Steel Coffee Maker"),
            Product(store=high, name="Sleek Stainless Steel Coffee Maker"),
            Product(store=high, name="Sleek Stainless Steel Coffee Maker"),
            Product(store=high, name="Eco-Friendly Bamboo Toothbrush Set"),
            Product(store=high, name="Eco-Friendly Bamboo Toothbrush Set"),
            Product(store=high, name="Eco-Friendly Bamboo Toothbrush Set"),
        ]
    )


def test_foo(products):
    print()
    print()
    print("***************")
    print()

    print(Product.objects.all().query)

    print()
    print("***************")
    print()
    print()


def test_no_group_by(products):
    assert "GROUP BY" not in str(Product.objects.all().query)


def test_legacy_group_by(products):
    results = (
        Product.objects.values("name")
        .annotate(total=Count("*"))
        .values("name", "total")
        .order_by("-total")
    )

    assert list(results) == [
        {"name": "Eco-Friendly Bamboo Toothbrush Set", "total": 8},
        {"name": "ProSeries Wireless Earbuds", "total": 7},
        {"name": "Sleek Stainless Steel Coffee Maker", "total": 6},
        {"name": "UltraComfort Memory Foam Mattress", "total": 4},
    ]


def test_group_by(products):
    results = (
        Product.objects.group_by("name")
        .values("name", total=Count("*"))
        .order_by("-total")
    )

    assert list(results) == [
        {"name": "Eco-Friendly Bamboo Toothbrush Set", "total": 8},
        {"name": "ProSeries Wireless Earbuds", "total": 7},
        {"name": "Sleek Stainless Steel Coffee Maker", "total": 6},
        {"name": "UltraComfort Memory Foam Mattress", "total": 4},
    ]


def test_incorrect_group_by_triggers_error():
    """
    Specifying group_by() disables the legacy inferred grouping, so it's up to the
    user to specify it correctly.
    """
    results = (
        Product.objects.group_by("store")
        .values("name", total=Count("*"))
        .order_by("-total")
    )

    with pytest.raises(
        ProgrammingError,
        match='column "explicit_group_by_product.name" must appear in the GROUP BY clause or be used in an aggregate function',
    ):
        list(results)


def test_rollup(products):
    """
    Demonstrate how to GROUP BY ROLLUP(<field>) to get a grand total along with the group totals.
    """
    results = (
        Product.objects.group_by(Func("name", function="rollup"))
        .values(category=Coalesce("name", Value("Total")), total=Count("*"))
        .order_by("-total")
    )

    assert list(results) == [
        {"category": "Total", "total": 25},
        {"category": "Eco-Friendly Bamboo Toothbrush Set", "total": 8},
        {"category": "ProSeries Wireless Earbuds", "total": 7},
        {"category": "Sleek Stainless Steel Coffee Maker", "total": 6},
        {"category": "UltraComfort Memory Foam Mattress", "total": 4},
    ]


def test_rollup_2_fields(products):
    """
    Demonstrate how to GROUP BY ROLLUP(<field 1>, <field 2>) to get both a grand total and subtotals per store
    along with the group totals.
    """
    results = (
        Product.objects.group_by(
            Func("store__location", "name", function="rollup", output_field=CharField())
        )
        .values(
            category=Case(
                When(store__location=None, name=None, then=Value("Grand Total")),
                When(name=None, then=Concat(F("store__location"), Value(" Total"))),
                default="name",
            ),
            total=Count("*"),
        )
        .order_by(
            OrderBy(F("store__location"), nulls_first=True),
            OrderBy(F("name"), nulls_first=True),
            "-total",
        )
    )

    assert list(results) == [
        # Grand Total
        {"category": "Grand Total", "total": 25},
        # High st subtotal
        {"category": "High st Total", "total": 14},
        {"category": "Eco-Friendly Bamboo Toothbrush Set", "total": 3},
        {"category": "ProSeries Wireless Earbuds", "total": 5},
        {"category": "Sleek Stainless Steel Coffee Maker", "total": 5},
        {"category": "UltraComfort Memory Foam Mattress", "total": 1},
        # Main st subtotal
        {"category": "Main st Total", "total": 11},
        {"category": "Eco-Friendly Bamboo Toothbrush Set", "total": 5},
        {"category": "ProSeries Wireless Earbuds", "total": 2},
        {"category": "Sleek Stainless Steel Coffee Maker", "total": 1},
        {"category": "UltraComfort Memory Foam Mattress", "total": 3},
    ]
