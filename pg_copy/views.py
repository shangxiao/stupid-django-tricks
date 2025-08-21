import csv
from zoneinfo import ZoneInfo

from django.core.exceptions import EmptyResultSet
from django.db import connection
from django.db.models import CharField, DateTimeField, F, Func, Value
from django.db.models.sql.where import WhereNode
from django.http import HttpResponse, JsonResponse
from django.utils.dateformat import DateFormat

from .models import Product


def mogrify_queryset(qs):
    with connection.cursor() as cur:
        try:
            return cur.mogrify(*qs.query.sql_with_params())

        except EmptyResultSet:
            # An EmptyResultSet means a filter was declared that's a logical contradiction
            # (ie that will never be true), for eg foo__in=[]
            #
            # We still need a query with a compatible select clause; in order to do
            # that we can clear the where clause and add "limit 0"
            # It's not ideal as it doesn't show the originally requested where clause
            # (ie if required for debugging purposes) but it functions equivalently
            # if required to execute by itself or interpolated in a larger query.

            query = qs.query.clone()
            query.where = WhereNode()
            return cur.mogrify(*query.sql_with_params()) + " LIMIT 0"


class YesNo(Func):
    template = "CASE WHEN %(expressions)s = TRUE THEN 'Yes' WHEN %(expressions)s = FALSE THEN 'No' ELSE '' END"
    output_field = CharField()
    arity = 1


class ChoiceDisplay(Func):
    output_field = CharField()

    def __init__(self, choices, *args, **kwargs):
        self.template = "CASE"
        self.template += "".join(
            [f" WHEN %(expressions)s = '{key}' THEN '{val}'" for key, val in choices]
        )
        self.template += " ELSE '' END"
        super().__init__(*args, **kwargs)


class ToChar(Func):
    function = "TO_CHAR"
    output_field = CharField()


class AtTimeZone(Func):
    template = "%(expressions)s AT TIME ZONE '%(timezone)s'"
    output_field = DateTimeField()
    arity = 1

    def __init__(self, *args, timezone="UTC", **kwargs):
        self.timezone = timezone
        super().__init__(*args, **kwargs)

    def as_sql(self, compiler, connection, template=None, **extra_context):
        extra_context["timezone"] = self.timezone
        return super().as_sql(compiler, connection, template, **extra_context)


def export(request):
    export_queryset = Product.objects.values(
        **{
            "SKU": F("sku"),
            "Name": F("name"),
            "Description": F("description"),
            "Category": F("category__name"),
            "Brand": F("brand__name"),
            "Price": F("price"),
            "Currency": F("currency"),
            "Stock Quantity": F("stock_qty"),
            "Availability": ChoiceDisplay(Product.Availability.choices, "availability"),
            "Is Active?": YesNo("is_active"),
            "Last Updated": ToChar(
                AtTimeZone("updated_at", timezone="Hongkong"),
                # be careful with the PG formatting! eg MI vs MM
                Value("FMDDth Mon YYYY FMHH:MI pm"),
            ),
            "Date Created": AtTimeZone("created_at", timezone="Hongkong"),
        }
        # Remember: references to columns must use the alias
    ).order_by("-Date Created")

    with connection.cursor() as cursor:
        # Optionally set the timezone for the session
        # cursor.execute("SET TIME ZONE 'Hongkong'")

        with cursor.copy(
            "COPY ({}) TO STDOUT WITH (FORMAT csv, HEADER)".format(
                mogrify_queryset(export_queryset)
            )
        ) as copy:
            return HttpResponse(
                copy,
                content_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="products.csv"'},
            )


def export_traditional(request):
    hk_timezone = ZoneInfo("Hongkong")
    products = Product.objects.select_related("category", "brand").order_by(
        "-created_at"
    )

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="products.csv"'},
    )

    writer = csv.writer(response, lineterminator="\n")
    writer.writerow(
        [
            "SKU",
            "Name",
            "Description",
            "Category",
            "Brand",
            "Price",
            "Currency",
            "Stock Quantity",
            "Availability",
            "Is Active?",
            "Last Updated",
            "Date Created",
        ]
    )
    for product in products:
        writer.writerow(
            [
                product.sku,
                product.name,
                product.description,
                product.category.name,
                product.brand.name if product.brand else "",
                product.price,
                product.currency,
                product.stock_qty,
                product.get_availability_display(),
                "Yes" if product.is_active else "No",
                DateFormat(product.updated_at.astimezone(hk_timezone)).format(
                    "jS M Y g:i "
                )
                + DateFormat(product.updated_at.astimezone(hk_timezone))
                .format("A")
                .lower(),
                product.created_at.astimezone(hk_timezone).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            ]
        )

    return response


def json(request):
    export_queryset = Product.objects.values(
        **{
            "SKU": F("sku"),
            "Name": F("name"),
            "Description": F("description"),
            "Category": F("category__name"),
            "Brand": F("brand__name"),
            "Price": F("price"),
            "Currency": F("currency"),
            "Stock Quantity": F("stock_qty"),
            "Availability": ChoiceDisplay(Product.Availability.choices, "availability"),
            "Is Active?": YesNo("is_active"),
            "Last Updated": ToChar(
                AtTimeZone("updated_at", timezone="Hongkong"),
                # be careful with the PG formatting! eg MI vs MM
                Value("FMDDth Mon YYYY FMHH:MI pm"),
            ),
            "Date Created": AtTimeZone("created_at", timezone="Hongkong"),
        }
        # Remember: references to columns must use the alias
    ).order_by("-Date Created")

    with connection.cursor() as cursor:
        # Optionally set the timezone for the session
        # cursor.execute("SET TIME ZONE 'Hongkong'")

        with cursor.copy(
            "COPY (SELECT jsonb_agg(t) FROM ({}) t) TO STDOUT WITH (FORMAT text)".format(
                mogrify_queryset(export_queryset)
            )
        ) as copy:
            return HttpResponse(
                copy,
                content_type="application/json",
            )


def json_traditional(request):
    hk_timezone = ZoneInfo("Hongkong")
    products = Product.objects.select_related("category", "brand").order_by(
        "-created_at"
    )
    return JsonResponse(
        data=[
            {
                "SKU": product.sku,
                "Name": product.name,
                "Description": product.description,
                "Category": product.category.name,
                "Brand": product.brand.name if product.brand else "",
                "Price": product.price,
                "Currency": product.currency,
                "Stock Quantity": product.stock_qty,
                "Availability": product.get_availability_display(),
                "Is Active?": "Yes" if product.is_active else "No",
                "Last Updated": DateFormat(
                    product.updated_at.astimezone(hk_timezone)
                ).format("jS M Y g:i ")
                + DateFormat(product.updated_at.astimezone(hk_timezone))
                .format("A")
                .lower(),
                "Date Created": product.created_at.astimezone(hk_timezone).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
            for product in products
        ],
        safe=False,
    )
