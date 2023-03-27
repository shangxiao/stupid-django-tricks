import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.utils import IntegrityError

from abusing_constraints.models import (
    ActiveDocument,
    ActiveDocumentByName,
    Bar,
    Child,
    Data,
    Document,
    Foo,
    Parent,
    Tenant,
)

pytestmark = pytest.mark.django_db


def test_constrained_tenant():
    tenant_1 = Tenant.objects.create()
    tenant_2 = Tenant.objects.create()
    foo_1 = Foo.objects.create(tenant=tenant_1)
    foo_2 = Foo.objects.create(tenant=tenant_2)

    # should be allowed
    Bar.objects.create(tenant=tenant_1, foo=foo_1)

    # should NOT be allowed
    with pytest.raises(IntegrityError):
        Bar.objects.create(tenant=tenant_1, foo=foo_2)


def test_fk_validate():
    tenant_1 = Tenant.objects.create()
    tenant_2 = Tenant.objects.create()
    foo = Foo.objects.create(tenant=tenant_1)
    bar = Bar.objects.create(tenant=tenant_1, foo=foo)

    # ok
    bar.validate_constraints()

    bar.tenant = tenant_2

    # now should fail validation
    with pytest.raises(ValidationError) as error:
        bar.validate_constraints()
    assert error.value.messages == ["Constraint “tenant_constraint” is violated."]


def test_intial_data_and_store_procedure():
    # Initial data provided through Callback should be 1, 2, 3
    assert list(Data.objects.values_list("data", flat=True)) == [1, 2, 3]

    with connection.cursor() as cursor:
        cursor.execute("CALL data_stored_procedure()")

    # The stored procedure should append 99
    assert list(Data.objects.values_list("data", flat=True)) == [1, 2, 3, 99]


def test_view():
    Document.objects.create(name="Active Document")
    Document.objects.create(name="Archived Document", is_archived=True)
    active_document = ActiveDocument.objects.first()

    # Assert our view reflects the source
    assert active_document.name == "Active Document"

    # Try updating the view!
    active_document.name = "Active Document has been updated!"
    active_document.save()
    active_document.refresh_from_db()

    assert active_document.name == "Active Document has been updated!"

    active_document_by_name = ActiveDocumentByName.objects.first()

    assert active_document_by_name.name == "Active Document has been updated!"


def test_database_level_cascading_deletes():
    parent = Parent.objects.create()
    child = Child.objects.create(parent=parent)

    parent.delete()

    with pytest.raises(Child.DoesNotExist):
        child.refresh_from_db()
