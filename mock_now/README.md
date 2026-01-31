Mocking now() within PostgreSQL
===============================

January 2026


Oftentimes developers would like to use `now()` in their SQL queries for convenience then find that testing is made more
difficult because you no longer have the benefit of "freezing" time by mocking the system's time with tools like
Freezgun.

Mocking objects in PostgreSQL can be done but it requires modifying the `search_path` to put `pg_catalog` last, which has
the effect of causing PG to look for system definitions of an object _after_ any user-defined ones.

```sql
=> SHOW search_path;
   search_path
-----------------
 "$user", public
(1 row)

=> SET search_path = "$user",public,pg_catalog;
SET
```

Then it's simply a matter of defining your own implementation:

```sql
=> SET search_path = "$user",public,pg_catalog;
SET
=> CREATE OR REPLACE FUNCTION public.now()
RETURNS timestamptz
LANGUAGE sql
STABLE
AS $$
    SELECT '2026-01-01 00:00:00+00'::timestamptz;
$$;
CREATE FUNCTION
=> select now();
          now
------------------------
 2026-01-01 11:00:00+11
(1 row)
```

It's much more useful if you can dymanically set what `now()` returns though. This can be done with a user defined
session vars:

```sql
=> SET search_path = "$user",public,pg_catalog;
SET
=> CREATE OR REPLACE FUNCTION public.now()
RETURNS timestamptz
LANGUAGE plpgsql
STABLE
AS $$
    DECLARE
        now_timestamp timestamptz;
    BEGIN
        SELECT coalesce(nullif(current_setting('my.now', true), '')::timestamptz, pg_catalog.now()) INTO now_timestamp;
        RETURN now_timestamp;
    END;
$$;
CREATE FUNCTION
=> SELECT now();
              now
-------------------------------
 2026-01-31 21:15:21.633949+00
(1 row)

=> SET "my.now" = '2026-01-01 00:00:00+11';
SET
=> SELECT now();
          now
------------------------
 2026-01-01 00:00:00+11
(1 row)
```

If you have any migrations that are dependent on `now()`, for eg in any views, then you'll need to set this mock up
before migrations are run using the `pre_migrate` signal. Check out [tests.py](./tests.py) for an example pytest
fixture.
