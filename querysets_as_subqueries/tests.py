import pytest
from django.db.models import Case, F, Q, Sum, Value, When
from django.db.models.expressions import OrderBy, Window
from django.db.models.functions import Lower, RowNumber, Upper

from .models import Sales, Shop, subqueryset

pytestmark = pytest.mark.django_db


def test_subquery_as_queryset():
    Shop.objects.create(name="KFC")
    Shop.objects.create(name="Pizza Hut")

    qs = subqueryset(
        subqueryset(
            subqueryset(
                Shop.objects.values("name"),
            )
            .annotate(name_upper=Upper("name"))
            .values("name", "name_upper"),
        )
        .annotate(name_lower=Lower("name_upper"))
        .values("name", "name_upper", "name_lower")
    )

    assert list(qs.values()) == [
        {"name": "KFC", "name_upper": "KFC", "name_lower": "kfc"},
        {"name": "Pizza Hut", "name_upper": "PIZZA HUT", "name_lower": "pizza hut"},
    ]


def test_calculate_top_3():
    kfc = Shop.objects.create(name="KFC")
    Sales.objects.create(shop=kfc, date="2000-01-01", sales=10)
    Sales.objects.create(shop=kfc, date="2000-01-02", sales=20)
    Sales.objects.create(shop=kfc, date="2000-01-03", sales=30)
    Sales.objects.create(shop=kfc, date="2000-01-04", sales=40)
    Sales.objects.create(shop=kfc, date="2000-01-05", sales=50)
    pizza_hut = Shop.objects.create(name="Pizza Hut")
    Sales.objects.create(shop=pizza_hut, date="2000-01-01", sales=10)
    Sales.objects.create(shop=pizza_hut, date="2000-01-02", sales=20)
    Sales.objects.create(shop=pizza_hut, date="2000-01-03", sales=30)
    Sales.objects.create(shop=pizza_hut, date="2000-01-04", sales=40)
    micky_ds = Shop.objects.create(name="McDonald's")
    Sales.objects.create(shop=micky_ds, date="2000-01-01", sales=10)
    Sales.objects.create(shop=micky_ds, date="2000-01-02", sales=20)
    Sales.objects.create(shop=micky_ds, date="2000-01-03", sales=30)
    # Others, no one shop is within the top 3 but the total of remaining is more than 3rd place...
    # do this to demonstrate order preservation
    hungry_jacks = Shop.objects.create(name="Hungry Jacks")
    Sales.objects.create(shop=hungry_jacks, date="2000-01-01", sales=10)
    Sales.objects.create(shop=hungry_jacks, date="2000-01-02", sales=20)
    grilld = Shop.objects.create(name="Grill'd")
    Sales.objects.create(shop=grilld, date="2000-01-01", sales=10)
    Sales.objects.create(shop=grilld, date="2000-01-02", sales=20)
    bettys = Shop.objects.create(name="Bettys")
    Sales.objects.create(shop=bettys, date="2000-01-01", sales=10)
    Sales.objects.create(shop=bettys, date="2000-01-02", sales=20)

    # here a forced subquery is required in order to make use of the row_number()
    qs = (
        subqueryset(
            Sales.objects.annotate(shop_name=F("shop__name"))
            .values("shop_name")
            .annotate(
                total_sales=Sum("sales"),
                order=Window(RowNumber()),
            )
            .order_by("-total_sales")
            .values("shop_name", "total_sales", "order")
        )
        .annotate(
            category=Case(
                When(condition=Q(order__gt=3), then=Value("Other")),
                default=F("shop_name"),
            ),
        )
        .values("category")
        .annotate(sales=Sum("total_sales"))
        .values("category", "sales")
        .order_by(
            OrderBy(Q(category=Value("Other"))),
            "-sales",
        )
        # Was originally using this order by utilising row_number() output but it's easier to simply force Other
        # to the bottom by asking "Is category == Other?"
        # (For this though we can't use 'order' directly as it will be added to the group by)
        # .order_by(
        #     Case(
        #         When(condition=Q(order__gt=3), then=Value(4)),
        #         default=F("order"),
        #     )
        # )
    )

    assert list(qs) == [
        {"category": "KFC", "sales": 150},
        {"category": "Pizza Hut", "sales": 100},
        {"category": "McDonald's", "sales": 60},
        {"category": "Other", "sales": 90},
    ]


class GenerateSeries:
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step


@pytest.mark.skip(
    "Nice to do in the future: pass arbitrary number of querysets with join conditions"
)
def test_left_join_onto_category_cartesian_product_with_series():
    series = GenerateSeries(start="2000-01-01", stop="2000-01-31", step="1 day")
    kfc = Shop.objects.create(name="KFC")
    Sales.objects.create(shop=kfc, date="2000-01-01", sales=10)
    Sales.objects.create(shop=kfc, date="2000-01-02", sales=20)
    Sales.objects.create(shop=kfc, date="2000-01-03", sales=30)
    Sales.objects.create(shop=kfc, date="2000-01-04", sales=40)
    Sales.objects.create(shop=kfc, date="2000-01-05", sales=50)
    pizza_hut = Shop.objects.create(name="Pizza Hut")
    Sales.objects.create(shop=pizza_hut, date="2000-01-01", sales=10)
    Sales.objects.create(shop=pizza_hut, date="2000-01-02", sales=20)
    Sales.objects.create(shop=pizza_hut, date="2000-01-03", sales=30)
    Sales.objects.create(shop=pizza_hut, date="2000-01-04", sales=40)
    micky_ds = Shop.objects.create(name="McDonald's")
    Sales.objects.create(shop=micky_ds, date="2000-01-01", sales=10)
    Sales.objects.create(shop=micky_ds, date="2000-01-02", sales=20)
    Sales.objects.create(shop=micky_ds, date="2000-01-03", sales=30)

    series_by_shops = subqueryset(series, Shop.objects.all())
    subqueryset(
        series_by_shops, Sales.objects.all()
    )  # need to left join this as sales is sparse
