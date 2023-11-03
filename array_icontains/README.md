Array icontains Lookup
======================

November 2023


A ticket was raised on the [Django Issue Tracker](https://code.djangoproject.com/ticket/34942) requesting a
case-insensive version of the array `contains` lookup.

Django's provides a few `contains` lookups out of the box which include one for [text
fields](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#std-fieldlookup-contains), which also has a
[case-insensitive variant](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#icontains), as well as one for
[PostgreSQL specific array fields](https://docs.djangoproject.com/en/5.0/ref/contrib/postgres/fields/#contains) which
doesn't have a case-insentive variant.

As noted by the feature requestor, we can achieve case-insensitive array contains by using `<operand> ILIKE
ANY(<array>)`.

Writing custom lookups is well [supported & documented](https://docs.djangoproject.com/en/5.0/howto/custom-lookups/).

Following that guide and adjusting the example for `ArrayField` as well as swapping lhs & rhs to the format we're after
given above, we can use something like the following:


```python
@ArrayField.register_lookup
class ArrayIContains(Lookup):
    lookup_name = "icontains"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = rhs_params + lhs_params
        return "%s ILIKE ANY(%s)" % (rhs, lhs), params
```
