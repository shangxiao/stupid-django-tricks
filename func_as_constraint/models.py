import textwrap

from django.db import models
from django.db.backends.postgresql.psycopg_any import sql as psycopg_any_sql
from django.db.models.expressions import Func

from abusing_constraints.constraints import RawSQL


def func_as_constraint(func_class):
    sql = textwrap.dedent(func_class.create_function).strip()
    if func_class.__doc__:
        comment = psycopg_any_sql.quote(textwrap.dedent(func_class.__doc__).strip())
        if sql[-1] != ";":
            sql += ";"
        sql += f"COMMENT ON FUNCTION {func_class.function} IS {comment};"
    return RawSQL(
        name=func_class.function,
        sql=sql,
        reverse_sql=f"DROP FUNCTION IF EXISTS {func_class.function}",
    )


class HelloWorld(Func):
    """
    Print hello world!
    """

    function = "hello_world"
    output_field = models.CharField()
    create_function = """\
        CREATE OR REPLACE FUNCTION hello_world()
        RETURNS varchar
        AS $$
        BEGIN
            RETURN 'Hello World!';
        END;
        $$ LANGUAGE plpgsql;
    """


class PlaceholderModel(models.Model):
    class Meta:
        constraints = [
            func_as_constraint(HelloWorld),
        ]
