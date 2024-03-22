from django.db import models


class DomainWhitelist(models.Model):
    domain = models.CharField(primary_key=True, max_length=255)

    def __str__(self):
        return self.domain
