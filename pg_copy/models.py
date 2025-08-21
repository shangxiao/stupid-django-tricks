from django.db import models
from django.db.models.query import QuerySet
from django.db.models.sql.query import Query


class NoCheckAliasQuery(Query):
    def check_alias(self, alias):
        pass


class Category(models.Model):
    name = models.CharField(unique=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(unique=True)

    def __str__(self):
        return self.name


class ProductQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        if not query:
            query = NoCheckAliasQuery(model)
        super().__init__(model, query, using, hints)


class Product(models.Model):
    objects = ProductQuerySet.as_manager()

    class Availability(models.TextChoices):
        IN_STOCK = "in_stock", "In Stock"
        PREORDER = "preorder", "Preorder"
        DISCONTINUED = "discontinued", "Discontinued"

    sku = models.CharField(unique=True, verbose_name="SKU")
    name = models.CharField()
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(db_default="USD")
    stock_qty = models.PositiveIntegerField(db_default=0, verbose_name="Stock quantity")

    availability = models.CharField(
        choices=Availability.choices,
        db_default=Availability.IN_STOCK,
    )

    is_active = models.BooleanField(db_default=True, verbose_name="Active?")
    created_at = models.DateTimeField(verbose_name="Created at")
    updated_at = models.DateTimeField(verbose_name="Updated at")

    def __str__(self):
        return f"{self.sku} — {self.name}"
