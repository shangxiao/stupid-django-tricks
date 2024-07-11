Functions as Constraints
========================

July 2024


We've seen that we can use the constraints API to add artifacts to the database. An interesting application
is to colocate the definition for custom functions defined as `Func`:


```python
class HelloWorld(Func):
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
```

Using a simple function we can create a `RawSQL` constraint defined in [Having Fun with Constraints](../abusing_constraints/)

```python
def func_as_constraint(func_class):
    sql = textwrap.dedent(func_class.create_function).strip()
    return RawSQL(
        name=func_class.function,
        sql=sql,
        ...
    )
```

A next step might be to create a reverse for RawSQL that drops the function:

```python
def func_as_constraint(func_class):
    sql = textwrap.dedent(func_class.create_function).strip()
    return RawSQL(
        name=func_class.function,
        sql=sql,
        reverse_sql=f"DROP FUNCTION IF EXISTS {func_class.function}",
    )
```

We can even go so far as to add a comment to the function if the function class has a docstring:

```python
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
```
