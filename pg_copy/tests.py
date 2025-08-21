import pytest
import io
import csv
import textwrap

from .models import Brand, Category, Product

pytestmark = pytest.mark.django_db


def ascii_grid_to_csv(table):
    """
    Convert an ASCII 'grid' table (like +---+---+ lines with | separators)
    directly into CSV text.
    """
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")

    for line in textwrap.dedent(table).splitlines():
        line = line.rstrip()
        if not line.startswith("|"):
            continue  # skip border lines
        cells = [c.strip() for c in line.split("|")[1:-1]]
        writer.writerow(cells)

    return out.getvalue()


@pytest.fixture
def products():
    Category.objects.bulk_create(
        [
            Category(name="Toys"),
            Category(name="Electronics"),
            Category(name="Home & Kitchen"),
        ]
    )
    Brand.objects.bulk_create(
        [
            Brand(name="Acme"),
            Brand(name="Globex"),
            Brand(name="Initech"),
        ]
    )
    Product.objects.bulk_create(
        [
            Product(
                sku="TOY-001",
                name="Wooden Train Set",
                description="Classic wooden train with tracks.",
                category=Category.objects.get(name="Toys"),
                brand=Brand.objects.get(name="Acme"),
                price=29.95,
                availability=Product.Availability.PREORDER.value,
                is_active=True,
                created_at="2000-01-01 12:00:00+08",
                updated_at="2000-01-01 12:00:00+08",
            ),
            Product(
                sku="TOY-002",
                name="Lego Starter Pack",
                description="Basic Lego bricks in assorted colors.",
                category=Category.objects.get(name="Toys"),
                brand=Brand.objects.get(name="Globex"),
                price=59.00,
                currency="EUR",
                stock_qty=80,
                is_active=False,
                created_at="2000-01-01 13:00:00+08",
                updated_at="2000-01-01 13:00:00+08",
            ),
            Product(
                sku="ELEC-001",
                name="Kids Headphones",
                description="Volume-limited headphones for children.",
                category=Category.objects.get(name="Electronics"),
                brand=None,  # no brand
                price=49.00,
                stock_qty=58,
                is_active=True,
                created_at="2000-01-01 14:00:00+08",
                updated_at="2000-01-01 14:00:00+08",
            ),
            Product(
                sku="HOME-001",
                name="Stainless Steel Water Bottle",
                description="1L insulated bottle, keeps drinks cold.",
                category=Category.objects.get(name="Home & Kitchen"),
                brand=Brand.objects.get(name="Initech"),
                price=19.95,
                stock_qty=200,
                is_active=True,
                created_at="2000-01-01 15:00:00+08",
                updated_at="2000-01-01 15:00:00+08",
            ),
        ]
    )


def test_csv_export(products, client):
    response = client.get("/pg_copy/export/")

    assert response.status_code == 200
    assert response.get("Content-Disposition") == 'attachment; filename="products.csv"'
    assert response.content.decode("utf-8") == ascii_grid_to_csv(
        """\
        +----------+------------------------------+-----------------------------------------+----------------+---------+-------+----------+----------------+--------------+------------+----------------------+---------------------+
        | SKU      | Name                         | Description                             | Category       | Brand   | Price | Currency | Stock Quantity | Availability | Is Active? | Last Updated         | Date Created        |
        +----------+------------------------------+-----------------------------------------+----------------+---------+-------+----------+----------------+--------------+------------+----------------------+---------------------+
        | HOME-001 | Stainless Steel Water Bottle | 1L insulated bottle, keeps drinks cold. | Home & Kitchen | Initech | 19.95 | USD      | 200            | In Stock     | Yes        | 1st Jan 2000 3:00 pm | 2000-01-01 15:00:00 |
        | ELEC-001 | Kids Headphones              | Volume-limited headphones for children. | Electronics    |         | 49.00 | USD      | 58             | In Stock     | Yes        | 1st Jan 2000 2:00 pm | 2000-01-01 14:00:00 |
        | TOY-002  | Lego Starter Pack            | Basic Lego bricks in assorted colors.   | Toys           | Globex  | 59.00 | EUR      | 80             | In Stock     | No         | 1st Jan 2000 1:00 pm | 2000-01-01 13:00:00 |
        | TOY-001  | Wooden Train Set             | Classic wooden train with tracks.       | Toys           | Acme    | 29.95 | USD      | 0              | Preorder     | Yes        | 1st Jan 2000 12:00 pm | 2000-01-01 12:00:00 |
        +----------+------------------------------+-----------------------------------------+----------------+---------+-------+----------+----------------+--------------+------------+----------------------+---------------------+
        """
    )


def test_csv_export_no_data(client):
    response = client.get("/pg_copy/export/")

    assert response.status_code == 200
    assert response.get("Content-Disposition") == 'attachment; filename="products.csv"'
    assert response.content.decode("utf-8") == ascii_grid_to_csv(
        """\
        +-----+------+-------------+----------+-------+-------+----------+----------------+--------------+------------+--------------+--------------+
        | SKU | Name | Description | Category | Brand | Price | Currency | Stock Quantity | Availability | Is Active? | Last Updated | Date Created |
        +-----+------+-------------+----------+-------+-------+----------+----------------+--------------+------------+--------------+--------------+
        """
    )


def test_traditional_export(products, client):
    response = client.get("/pg_copy/export-traditional/")

    assert response.status_code == 200
    assert response.get("Content-Disposition") == 'attachment; filename="products.csv"'
    assert response.content.decode("utf-8") == ascii_grid_to_csv(
        """\
        +----------+------------------------------+-----------------------------------------+----------------+---------+-------+----------+----------------+--------------+------------+----------------------+---------------------+
        | SKU      | Name                         | Description                             | Category       | Brand   | Price | Currency | Stock Quantity | Availability | Is Active? | Last Updated         | Date Created        |
        +----------+------------------------------+-----------------------------------------+----------------+---------+-------+----------+----------------+--------------+------------+----------------------+---------------------+
        | HOME-001 | Stainless Steel Water Bottle | 1L insulated bottle, keeps drinks cold. | Home & Kitchen | Initech | 19.95 | USD      | 200            | In Stock     | Yes        | 1st Jan 2000 3:00 pm | 2000-01-01 15:00:00 |
        | ELEC-001 | Kids Headphones              | Volume-limited headphones for children. | Electronics    |         | 49.00 | USD      | 58             | In Stock     | Yes        | 1st Jan 2000 2:00 pm | 2000-01-01 14:00:00 |
        | TOY-002  | Lego Starter Pack            | Basic Lego bricks in assorted colors.   | Toys           | Globex  | 59.00 | EUR      | 80             | In Stock     | No         | 1st Jan 2000 1:00 pm | 2000-01-01 13:00:00 |
        | TOY-001  | Wooden Train Set             | Classic wooden train with tracks.       | Toys           | Acme    | 29.95 | USD      | 0              | Preorder     | Yes        | 1st Jan 2000 12:00 pm | 2000-01-01 12:00:00 |
        +----------+------------------------------+-----------------------------------------+----------------+---------+-------+----------+----------------+--------------+------------+----------------------+---------------------+
        """
    )
