import pytest
from django.db.models import F

from .models import Product, Shop

pytestmark = pytest.mark.django_db


def test_cartesian_product():
    kfc = Shop.objects.create(name="KFC")
    Product.objects.create(name="Original Recipe", shop=kfc)
    Product.objects.create(name="Hot n Spicy Wings", shop=kfc)
    pizza_hut = Shop.objects.create(name="Pizza Hut")
    Product.objects.create(name="Super Supreme", shop=pizza_hut)
    Product.objects.create(name="Capricciosa", shop=pizza_hut)
    shops = Shop.objects.all().values("id", "name")
    products = Product.objects.all().values("name", "shop_id")

    qs = (shops * products).filter(shop_name="KFC", shop_id=F("product_shop_id"))

    assert list(qs.values()) == [
        {
            "id": 1,
            "shop_id": 1,
            "shop_name": "KFC",
            "product_name": "Original Recipe",
            "product_shop_id": 1,
        },
        {
            "id": 2,
            "shop_id": 1,
            "shop_name": "KFC",
            "product_name": "Hot n Spicy Wings",
            "product_shop_id": 1,
        },
    ]
