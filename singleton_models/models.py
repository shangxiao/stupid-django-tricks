from django.db import models


class Settings(models.Model):
    the_singleton = models.BooleanField(primary_key=True, default=True)
    setting_a = models.CharField(max_length=255, blank=True, default='Setting A')
    setting_b = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = (
            models.CheckConstraint(
                name="singleton",
                check=models.Q(the_singleton=True),
            ),
        )

    @classmethod
    def get(cls):
        return cls.objects.get_or_create(the_singleton=True)[0]
