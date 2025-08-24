from django.db import models


class Data(models.Model):
    value = models.IntegerField()
