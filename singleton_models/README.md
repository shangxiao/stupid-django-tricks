Singleton Models
================

A [Singleton](https://en.wikipedia.org/wiki/Singleton_pattern) is a design pattern
to ensure that a single instance of a class only ever exists. This may be useful for numerous
reasons but possibly most popularly for storing application settings. For web applications
storing this data in the database may be the most convenient, thereby creating the
need for a singleton database model.

The simplest way to create a singleton table in Postgres that I could find was
to simply add a constant with a unique + check constraint to ensure that only
one row exists with the specified constant value:

```sql
CREATE TABLE settings (
    singleton boolean NOT NULL DEFAULT 't' PRIMARY KEY CHECK (singleton),
    setting_a varchar DEFAULT 'Setting A',
    setting_b varchar
);
```

This would translate to the following in Django (noting that the default is
only referred to at the ORM-level):

```python
class Settings(models.Model):
    the_singleton = models.BooleanField(primary_key=True, default=True)
    setting_a = models.CharField(max_length=255, blank=True, default="Setting A")
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
```

```
> settings = Settings.get()
> settings.setting_a
'Setting A'
> settings.setting_b = 'Setting B'
> settings.save()
> Settings.objects.create()
django.db.utils.IntegrityError: UNIQUE constraint failed: singleton_models_settings.the_singleton
> Settings.objects.create(the_singleton=False)
django.db.utils.IntegrityError: CHECK constraint failed: singleton
```

You could extend this to add a trigger to prevent deletion of the settings row or simply treat deleting as a way of clearing the settings back to system defaults.
