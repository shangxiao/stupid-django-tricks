Xor Function
============

December 2023


Django 5.0 changes the XOR emulation on databases that don't have an XOR operator like PostgreSQL so that the result is
no longer "1 and only 1 operand should be true" to "An odd number of operands should be true". This brings it inline
with the true nature of how XOR behaves when acting as a binary operator.

I find, however, that the behaviour XOR as a ternary operator to be far more useful for checks to ensure that only 1
expression be true. For example you may have 3 nullable fields but only one should be set depending on indicating some
state of the record.

Moving forward folks wishing to preserve the older behaviour will need to write their own implementation. The options
are to either copy & paste the old `__xor__()` method code and [reverting the patches
here](https://github.com/django/django/commit/b81e974e9ea16bd693b194a728f77fb825ec8e54) or to simply define a function
that sums the true expressions and checking the result is equal to 1.

For a function that will only be used in check constraints and not in queries (including check constraint validation)
then all we need to do is modify a `Func` slightly to cast the arguments to integer, use `+` as the joiner then finally
update the template to check equality to `1`:

```python
class Xor(Func):
    template = "(%(expressions)s) = 1"
    arg_joiner = " + "
    output_field = models.BooleanField()

    def __init__(self, *expressions, output_field=None, **extra):
        super().__init__(
            *[Cast(e, models.IntegerField()) for e in expressions],
            output_field=output_field,
            **extra
        )
```

To be useful in queries such as check constraint validation then we need to consider that the supplied expressions will
raise an `EmptyResultSet`. `Func` already assumes a value of `True` for `FullResultSet` so we need to tell it to use `0`
for `EmptyResultSet`:

```python
class Xor(Func):
    template = "(%(expressions)s) = 1"
    arg_joiner = " + "
    output_field = models.BooleanField()

    def __init__(self, *expressions, output_field=None, **extra):
        updated_expressions = []
        for e in expressions:
            updated_expression = Cast(e, models.IntegerField())
            updated_expression.empty_result_set_value = 0
            updated_expressions.append(updated_expression)

        super().__init__(*updated_expressions, output_field=output_field, **extra)
```
