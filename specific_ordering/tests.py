import pytest
from django.db.models import Case, OrderBy, Q, When
from django.db.models.expressions import Func

from .models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def orders():
    Order.objects.bulk_create(
        [
            Order(product="UltraComfort Memory Foam Mattress", status="DELIVERED"),
            Order(product="ProSeries Wireless Earbuds", status="IN_PROGRESS"),
            Order(product="Sleek Stainless Steel Coffee Maker", status="SHIPPED"),
            Order(product="Eco-Friendly Bamboo Toothbrush Set", status="DELIVERED"),
            Order(product="Smart LED Desk Lamp with USB Charging", status="PAID"),
            Order(product="Luxury Cotton Bath Towel Set", status="PAID"),
            Order(product="Heavy-Duty Cordless Power Drill", status="IN_PROGRESS"),
            Order(product="Premium Leather Crossbody Bag", status="SHIPPED"),
            Order(product="Bluetooth Fitness Tracker Watch", status="DELIVERED"),
            Order(product="Foldable Portable Laptop Stand", status="DELIVERED"),
        ]
    )


def test_specific_order_with_case(orders):
    orders = Order.objects.order_by(
        Case(
            When(status="IN_PROGRESS", then=1),
            When(status="PAID", then=2),
            When(status="SHIPPED", then=3),
            When(status="DELIVERED", then=4),
            default=100,
        )
    )

    assert list(orders.values("product", "status")) == [
        {"product": "Heavy-Duty Cordless Power Drill", "status": "IN_PROGRESS"},
        {"product": "ProSeries Wireless Earbuds", "status": "IN_PROGRESS"},
        {"product": "Smart LED Desk Lamp with USB Charging", "status": "PAID"},
        {"product": "Luxury Cotton Bath Towel Set", "status": "PAID"},
        {"product": "Premium Leather Crossbody Bag", "status": "SHIPPED"},
        {"product": "Sleek Stainless Steel Coffee Maker", "status": "SHIPPED"},
        {"product": "Foldable Portable Laptop Stand", "status": "DELIVERED"},
        {"product": "Eco-Friendly Bamboo Toothbrush Set", "status": "DELIVERED"},
        {"product": "Bluetooth Fitness Tracker Watch", "status": "DELIVERED"},
        {"product": "UltraComfort Memory Foam Mattress", "status": "DELIVERED"},
    ]


def test_specific_order_with_direct_comparison(orders):
    orders = Order.objects.order_by(
        OrderBy(Q(status="IN_PROGRESS"), descending=True),
        OrderBy(Q(status="PAID"), descending=True),
        OrderBy(Q(status="SHIPPED"), descending=True),
        OrderBy(Q(status="DELIVERED"), descending=True),
    )

    assert list(orders.values("product", "status")) == [
        {"product": "Heavy-Duty Cordless Power Drill", "status": "IN_PROGRESS"},
        {"product": "ProSeries Wireless Earbuds", "status": "IN_PROGRESS"},
        {"product": "Smart LED Desk Lamp with USB Charging", "status": "PAID"},
        {"product": "Luxury Cotton Bath Towel Set", "status": "PAID"},
        {"product": "Premium Leather Crossbody Bag", "status": "SHIPPED"},
        {"product": "Sleek Stainless Steel Coffee Maker", "status": "SHIPPED"},
        {"product": "Foldable Portable Laptop Stand", "status": "DELIVERED"},
        {"product": "Eco-Friendly Bamboo Toothbrush Set", "status": "DELIVERED"},
        {"product": "Bluetooth Fitness Tracker Watch", "status": "DELIVERED"},
        {"product": "UltraComfort Memory Foam Mattress", "status": "DELIVERED"},
    ]


def test_specific_order_with_array_position(orders):
    orders = Order.objects.order_by(
        Func(
            ["IN_PROGRESS", "PAID", "SHIPPED", "DELIVERED"],
            "status",
            function="array_position",
        )
    )

    assert list(orders.values("product", "status")) == [
        {"product": "Heavy-Duty Cordless Power Drill", "status": "IN_PROGRESS"},
        {"product": "ProSeries Wireless Earbuds", "status": "IN_PROGRESS"},
        {"product": "Smart LED Desk Lamp with USB Charging", "status": "PAID"},
        {"product": "Luxury Cotton Bath Towel Set", "status": "PAID"},
        {"product": "Premium Leather Crossbody Bag", "status": "SHIPPED"},
        {"product": "Sleek Stainless Steel Coffee Maker", "status": "SHIPPED"},
        {"product": "Foldable Portable Laptop Stand", "status": "DELIVERED"},
        {"product": "Eco-Friendly Bamboo Toothbrush Set", "status": "DELIVERED"},
        {"product": "Bluetooth Fitness Tracker Watch", "status": "DELIVERED"},
        {"product": "UltraComfort Memory Foam Mattress", "status": "DELIVERED"},
    ]
