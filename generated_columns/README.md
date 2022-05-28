Generated Columns
=================

Generated columns (aka computed columns) are a feature of many databases including
[PostgreSQL](https://www.postgresql.org/docs/current/ddl-generated-columns.html).


Using a couple of [hacks](./models.py), we can get partial generated column support in Django:


```python
class GeneratedIntegerField(GeneratedColumnMixin, models.IntegerField):
    ...


class Squared(models.Model):
    operand = models.IntegerField()
    result = GeneratedIntegerField(expression="operand * operand")
```

In the shell with query logging enabled:

```pycon
>>> Squared.objects.create(operand=2).result
(0.002) INSERT INTO "generated_columns_squared" ("operand") VALUES (2) RETURNING "generated_columns_squared"."id", "generated_columns_squared"."result"; args=(2,); alias=default
4

>>> Squared.objects.get(operand=2).result
(0.002) SELECT "generated_columns_squared"."id", "generated_columns_squared"."operand", "generated_columns_squared"."result" FROM "generated_columns_squared" WHERE "generated_columns_squared"."operand" = 2 LIMIT 21; args=(2,); alias=default
4
```

Run the [tests](./tests.py) for a demonstration.


A More Practical Example
------------------------

Enforcing user emails a part of an admin-managed domain whitelist.

By taking advantage of the fact that generated columns can both be source and target in a foreign key
in PostgreSQL, we can create a solid constraint in the database with an indirect relationship between 2 tables:

```python
class DomainForeignKey(GeneratedColumnMixin, models.ForeignKey):
    def get_attname_column(self):
        return self.get_attname(), self.name


class DomainWhitelist(models.Model):
    domain = models.CharField(primary_key=True, max_length=254)

    def __str__(self):
        return self.domain


class Person(models.Model):
    email = models.EmailField(unique=True)
    email_domain = DomainForeignKey(
        DomainWhitelist,
        expression="substring(email from '@(.*)$')",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.email
```

```pycon
>>> DomainWhitelist.objects.create(domain="good.com")
<DomainWhitelist: good.com>

>>> Person.objects.create(email="fred@bad.com")
 ...
django.db.utils.IntegrityError: insert or update on table "generated_columns_person" violates foreign key constraint "generated_columns_pe_email_domain_61c60207_fk_generated"
DETAIL:  Key (email_domain)=(bad.com) is not present in table "generated_columns_domainwhitelist".

>>> Person.objects.create(email="joe@good.com")
<Person: joe@good.com>

>>> DomainWhitelist.objects.all().delete()
 ...
django.db.models.deletion.ProtectedError: ("Cannot delete some instances of model 'DomainWhitelist' because they are referenced through protected foreign keys: 'Person.email_domain'.", {<Person: joe@good.com>})
```


Notes
-----

For an ORM to take advantage of generated columns it would need to consider:
 - A field type that extends the database type to include the `GENERATED` syntax & expression to compute
 - Use of the `RETURNING` clause in both `INSERT` and `UPDATE` statements
 - Selectively include or ignore the field when fetching and either creating or updating a record respectively
 - Include the field in any migration management

Django can partially support generated fields:
 - Custom field types can include the `GENERATED` syntax & expression without any issue
 - Django already makes use of `RETURNING` to retrieve the primary key value during a create operation. Fields
   can set `db_returning = True`.

A hack can be applied to:
 - Make Django include the field for fetches and exclude the field for creates & updates via the `private_only`
   parameter of field's `contribute_to_class()` method. This is a hack because "private" fields are meant for
   use with Django's inheritance model, but it just so happens that it causes Django to select the field for
   insert/update/fetches in a way that is useful for generated columns.
 - An additional, rather dirty, hack can be used to skip the above hack during migration auto-detection & migrate
   operations.

Django does not:
 - Make use of the `RETURNING` clause during an update, meaning that running `instance.save()` will not update the field.
 - Check fields in the same manner of fetching & updating when using a queryset's `update()` meaning that Django
   will happily let you try to do `Squared.objects.update(result=0)` (Postgres will raise an error).
