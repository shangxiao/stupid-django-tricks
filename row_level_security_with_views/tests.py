import pytest
from django.db import transaction
from django.db.utils import IntegrityError, ProgrammingError

from set_config.tests import set_config_3

from .models import (
    Account,
    AccountView,
    Authorisation,
    Product,
    ProductView,
    Tenant,
    User,
)

# What about global admin use cases?

# Idea: can you define the concrete tables in one schema with superuser access
# and define the limited views in another schema with restricted access?


# postgres.fm episode talks about some of this


# notes on updateableness:
#
# if you only need to specify a tenant id
#  - simple views updatable requires all tables have the tenant id which is manageable
#  - views with auth check across tables then require triggers
#
# if you specify user id and fetch possibly multiple tenant ids
#  - not updatable


@pytest.fixture
def data():
    bank_1 = Tenant.objects.create(name="First National Bank")
    bank_2 = Tenant.objects.create(name="Second National Bank")

    Account.objects.create(name="Joe", tenant=bank_1)
    Account.objects.create(name="Frank", tenant=bank_2)

    yield bank_1, bank_2


@pytest.mark.django_db
def test_rls_no_setting(data):
    assert list(AccountView.objects.all()) == []


@pytest.mark.django_db(transaction=True)
def test_rls_with_setting(data):
    bank_1, bank_2 = data
    with transaction.atomic():
        set_config_3("app.tenant_id", bank_1.pk)
        assert list(AccountView.objects.values_list("name", flat=True)) == ["Joe"]

    assert list(AccountView.objects.all()) == []


@pytest.mark.django_db
def test_rls_insert(data):
    bank_1, bank_2 = data
    with transaction.atomic():
        set_config_3("app.tenant_id", bank_1.pk)
        AccountView.objects.create(name="Bob")
        assert list(AccountView.objects.values_list("name", flat=True)) == [
            "Joe",
            "Bob",
        ]


@pytest.mark.django_db
def test_rls_insert_no_tx(data):
    with pytest.raises(IntegrityError):
        AccountView.objects.create(name="Bob")


@pytest.fixture
def multi_data():
    bank_1 = Tenant.objects.create(name="First National Bank")
    bank_2 = Tenant.objects.create(name="Second National Bank")

    Product.objects.create(name="Loan from First National Bank", tenant=bank_1)
    Product.objects.create(name="Loan from Second National Bank", tenant=bank_2)

    yield bank_1, bank_2


@pytest.mark.django_db(transaction=True)
def test_rls_multiple_tenants(multi_data):
    bank_1, bank_2 = multi_data
    user = User.objects.create(name="Joe")
    Authorisation.objects.create(user=user, tenant=bank_1)
    with transaction.atomic():
        set_config_3("app.user", user.pk)
        assert list(ProductView.objects.values_list("name", flat=True)) == [
            "Loan from First National Bank"
        ]
    assert list(ProductView.objects.values_list("name", flat=True)) == []


# TIL that you can have a subquery in a view and it's still updatable??


# triggers can be disabled, but is that any worse than what can be currently achieved


@pytest.mark.django_db
def test_rls_insert_multiple_tenants(multi_data):
    bank_1, bank_2 = multi_data
    user = User.objects.create(name="Joe")
    Authorisation.objects.create(user=user, tenant=bank_1)
    with transaction.atomic():
        set_config_3("app.user", user.pk)
        ProductView.objects.create(name="New Product", tenant=bank_1)  # ok
        with transaction.atomic(), pytest.raises(ProgrammingError):
            ProductView.objects.create(
                name="Another New Product", tenant=bank_2
            )  # not ok
        assert list(Product.objects.values_list("name", flat=True)) == [
            "Loan from First National Bank",
            "Loan from Second National Bank",
            "New Product",
        ]
