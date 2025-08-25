Custom Postgres Parameters as a Context Manager
===============================================

August 2025


Custom Postgres session params:

 - Postgres has very basic parameter management which is designed for system administration
   - ref: https://www.postgresql.org/docs/current/functions-admin.html
 - Custom parameters are allowed using the dot syntax, eg: `'app.user'`
   - ref: https://www.postgresql.org/docs/current/runtime-config-custom.html
 - These are a way to pass application users to feature like RLS or RLS-like views as an alternative to the
   `current_user` placeholder.
 - Parameters are only either global to the session or isolated to a transaction, meaning that some manual resetting
   will be required if setting within transactions is required.
    - ref: https://www.postgresql.org/docs/current/sql-set.html
 - Both session & local parameters are reset upon errors (rollback transaction AND savepoints)
 - Since this feature wasn't really designed for general purpose parameter usage and the rather limited isolation, one
   need to take extreme care when using for security related features.


Given the warning in the last point above, a possible implementation might look like:

```python
@contextlib.contextmanager
def set_config(param, value):
    # Start transaction & set local as a bit of an extra safeguard. Even when used after a savepoint, an error will
    # also rollback the parameter (but not upon success however).
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("select current_setting('app.user', true)")
            prior_value = cursor.fetchone()[0]

            cursor.execute("select set_config(%s, %s, true)", [param, str(value)])

            def get_config():
                cursor.execute("select current_setting(%s, true)", [param])
                return type(value)(cursor.fetchone()[0])

            yield get_config

            cursor.execute(
                "select set_config(%s, %s, true)",
                [param, "" if prior_value is None else str(prior_value)],
            )
```
