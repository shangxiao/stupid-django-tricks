Django + `pg_cron`
==================

November 2024


Notes
 - https://github.com/citusdata/pg_cron
 - `pg_cron` is available in a lot of hosted PG solutions including RDS
 - `pg_cron` can only be installed into a single database, this is declared in `postgresql.conf`
 - Even if you define the cron jobs in the same DB as your application, unit tests will be hard to run with full
   integration, so perhaps the only kinds of tests are those that mock any required cron behaviour
