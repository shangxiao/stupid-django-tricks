from django.db import models
from django.db.models import Q
from django.db.models.constraints import CheckConstraint
from django.db.models.sql import Query


class ColumnCheckConstraint(CheckConstraint):
    # A dummy check constraint to simply handle validation

    def constraint_sql(self, model, schema_editor):
        return None

    def create_sql(self, model, schema_editor):
        return None

    def remove_sql(self, model, schema_editor):
        return None


class ColumnCheckMixin:
    def __init__(self, *args, check=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_check = check

    def db_check(self, connection):
        query = Query(self.model)
        query.add_q(self.column_check)
        compiler = query.get_compiler(using=connection.alias)
        sql, params = query.where.as_sql(compiler, connection.alias)
        with connection.cursor() as cursor:
            return cursor.mogrify(sql, params).decode("utf-8")

    def contribute_to_class(self, cls, name, private_only=False):
        # Use a dummy constraint to simply handle validation.
        if self.column_check:
            cls._meta.constraints.append(
                ColumnCheckConstraint(check=self.column_check, name=f"check_{name}")
            )
        super().contribute_to_class(cls, name, private_only)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["check"] = self.column_check
        return name, path, args, kwargs


class TableCheckMixin:
    def __init__(self, *args, check=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_check = check

    def contribute_to_class(self, cls, name, private_only=False):
        # Create the check as a table check constraint.
        if self.column_check:
            constraint = CheckConstraint(check=self.column_check, name=f"check_{name}")
            cls._meta.constraints += [constraint]
            if "constraints" in cls._meta.original_attrs:
                cls._meta.original_attrs["constraints"] += [constraint]
            else:
                cls._meta.original_attrs["constraints"] = [constraint]
        super().contribute_to_class(cls, name, private_only)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["check"] = self.column_check
        return name, path, args, kwargs


class CheckedIntegerField(ColumnCheckMixin, models.IntegerField):
    ...


class Project(models.Model):
    percentage = CheckedIntegerField(check=Q(percentage__gte=0, percentage__lte=100))
