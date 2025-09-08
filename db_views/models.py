from django.db import models


#
# - serialize querysets
# - detect meta changes
# - schema editor
#


class Account(models.Model):
    name = models.CharField()
    is_active = models.BooleanField(db_default=True)


class ActiveAccount(models.Model):
    name = models.CharField()

    class Meta:
        db_view = True
        query = Account.objects.filter(is_active=True, name=models.Value("foo"))
        materialized = True
