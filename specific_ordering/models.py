from django.db import models


class OrderStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"


class Order(models.Model):
    product = models.CharField()
    status = models.CharField(choices=OrderStatus.choices)
