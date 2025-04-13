from django.db import models
from django.db.models import Func, IntegerField, OrderBy


class OrderStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"


class Order(models.Model):
    product = models.CharField()
    status = models.CharField(choices=OrderStatus.choices)


class ArrayPosition(Func):
    function = "array_position"
    output_field = IntegerField()


class OrderByValue(OrderBy):
    def __init__(self, field, order, *args, **kwargs):
        super().__init__(ArrayPosition(order, field), *args, **kwargs)
