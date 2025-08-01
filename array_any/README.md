Array ANY Lookup
================

August 2025


When testing for `ArrayField` membership in Django you can used the supplied "contains" (or "overlap") lookups which map
directly to PostgreSQL operators.

If you don't feel like constructing an array the standard way to check for array membership is to use the `ANY`
operator, eg:

```
SELECT 1 = ANY ('{1,2,3}'::int[]);   -- true

SELECT 4 = ANY ('{1,2,3}'::int[]);   -- false
```

The correct way to negate this is to prepend with `NOT` and not use `!=` like so:

```
SELECT NOT 4 = ANY ('{1,2,3}'::int[]);   -- true
```

Similar to the array icontains lookup, we can simply define a custom lookup to support this:

```python
@ArrayField.register_lookup
class ArrayAny(Lookup):
    lookup_name = "any"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = rhs_params + lhs_params
        return "%s = ANY(%s)" % (rhs, lhs), params
```

Negating any query with this using `~Q()` will use the correct `NOT <value> = ANY <array>` approach.
