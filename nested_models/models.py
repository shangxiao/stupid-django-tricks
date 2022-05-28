import re

from django.db import models
from django.db.models.base import ModelBase

existing_new = ModelBase.__new__


# We're updating the metaclass in order to add this new field


def __new__(cls, name, bases, attrs, **kwargs):
    # Be sure to only process models from this app.
    # This is all very hacky of course - one cannot tell what 3rd party apps are added
    # that also use nested models... but hey this is a stupid django trick afterall.
    if "." in attrs.get("__qualname__", "") and attrs["__module__"].startswith(
        "nested_models"
    ):
        parent_class = attrs["__qualname__"].rsplit(".")[-2]
        parent_fk_name = re.sub(r"(?<!^)(?=[A-Z])", "_", parent_class).lower()
        attrs[parent_fk_name] = models.ForeignKey(
            parent_class, on_delete=models.CASCADE
        )

    return existing_new(cls, name, bases, attrs, **kwargs)


ModelBase.__new__ = __new__


class Parent(models.Model):
    class Child(models.Model):
        ...
