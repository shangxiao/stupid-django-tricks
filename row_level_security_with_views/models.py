from django.db import models
from django.db.models.expressions import RawSQL

from abusing_constraints.constraints import RawSQL as RawSQLConstraint
from abusing_constraints.constraints import View


class Tenant(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name


class Account(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_default=RawSQL(
            "nullif(current_setting('app.tenant_id'), '')::int", params=[]
        ),
    )
    name = models.CharField()

    def __str__(self):
        return self.name

    class Meta:
        constraints = []


class AccountView(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "account_view"
        # maybe have a managed model that migrations are purely just updating the view??
        managed = False


Account._meta.constraints += [
    View(
        name="account_view",
        query="select * from row_level_security_with_views_account where tenant_id = nullif(current_setting('app.tenant_id', true), '')::int",
        # query=Account.objects.filter(
        #     tenant_id=RawSQL("current_setting('app.tenant_id')::int", [])
        # ),
    ),
]

# insert triggers:
# option 1: hide tenant and trigger gets tenant from current_setting()
# option 2: show tenant and enfource new tenant = current_setting()
#  ^ both of these require a verbose trigger though because you have to specify all the columns >:|
# option 3: just specify a default using current_setting()


define_tenant_id = """\
CREATE OR REPLACE FUNCTION define_tenant_id() RETURNS trigger AS $$
BEGIN
    NEW.tenant_id = nullif(current_setting('app.tenant_id', true), '')::int;
    INSERT INTO row_level_security_with_views_account SELECT NEW;
    RETURN NULL;
END
$$ LANGUAGE plpgsql;
"""

account_view_insert_trigger = """\
CREATE OR REPLACE TRIGGER account_view_insert_trigger
INSTEAD OF insert ON account_view
FOR EACH ROW
EXECUTE FUNCTION define_tenant_id()
"""

# Account._meta.constraints += [
#     RawSQL(
#         name="define_tenant_id",
#         sql=define_tenant_id,
#         reverse_sql="DROP FUNCTION IF EXISTS define_tenant_id",
#     ),
#     RawSQL(
#         name="account_view_insert_trigger",
#         sql=account_view_insert_trigger,
#         reverse_sql="DROP TRIGGER IF EXISTS account_view_insert_trigger ON account_view",
#     ),
# ]


class User(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name


class Authorisation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("user", "tenant")]


class Product(models.Model):
    name = models.CharField()
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        # can't do this with multiple tenants
        # db_default=RawSQL(
        #     "nullif(current_setting('app.tenant_id'), '')::int", params=[]
        # ),
    )

    class Meta:
        constraints = []

    def __str__(self):
        return self.name


class ProductView(models.Model):
    name = models.CharField()
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        db_table = "product_view"
        managed = False

    def __str__(self):
        return self.name


Product._meta.constraints += [
    View(
        name="product_view",
        # should the select * be restricted here?
        query="select * from row_level_security_with_views_product where tenant_id in (select tenant_id from row_level_security_with_views_authorisation where user_id = nullif(current_setting('app.user', true), '')::int)",
    ),
]

# maybe this should be a constraint trigger?
check_tenant_id = """\
CREATE OR REPLACE FUNCTION check_tenant_id() RETURNS trigger AS $$
DECLARE
    myrec record;
BEGIN
    SELECT * INTO myrec FROM row_level_security_with_views_authorisation WHERE tenant_id = NEW.tenant_id AND user_id = nullif(current_setting('app.user', true), '')::int;
    IF FOUND THEN
        RETURN NEW;
    END IF;
    IF nullif(current_setting('app.user', true), '') IS NULL THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'Not authorised';
END
$$ LANGUAGE plpgsql;
"""

product_insert_trigger = """\
CREATE OR REPLACE TRIGGER product_insert_trigger
BEFORE insert ON row_level_security_with_views_product
FOR EACH ROW
EXECUTE FUNCTION check_tenant_id()
"""

Product._meta.constraints += [
    RawSQLConstraint(
        name="check_tenant_id",
        sql=check_tenant_id,
        reverse_sql="DROP FUNCTION IF EXISTS check_tenant_id",
    ),
    RawSQLConstraint(
        name="product_insert_trigger",
        sql=product_insert_trigger,
        reverse_sql="DROP TRIGGER IF EXISTS product_insert_trigger ON row_level_security_with_views_product",
    ),
]
