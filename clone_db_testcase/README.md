CloneDbTestCase
===============

March 2024


There are certain times in Django when you may be required to avoid transactions while writing tests, for such cases you
can use
[`TransactionTestCase`](https://docs.djangoproject.com/en/5.0/topics/testing/tools/#django.test.TransactionTestCase).
Despite the name, `TransactionTestCase` does not use transactions but rather flushes all tables upon test teardown along
with an optional ["rollback
 emulation"](https://docs.djangoproject.com/en/5.0/topics/testing/overview/#rollback-emulation)

The one thing this does **not** yet do is preserve initial data loaded via migrations when `--keepdb` is specified.

If we want rollback emulation to include preserving data we can write our own extension of `TransactionTestCase` that
clones the test DB and runs each test in this new clone effectively isolating the test.

Cloning test DBs is achieved by:
 - On PostgreSQL cloning is done by the `CREATE DATABASE ... WITH TEMPLATE ...` feature
 - On SQLite it's done with `source.backup(target)` though we have to do this manually as some assumptions are made
   that cloning is done within the context of parallel processing
 - On MySQL each clone is setup with `mysqldump`

A couple of notes regarding `TransactionTestCase` attributes when using this approach:
 - `fixtures`: loading of fixtures can either be done during db setup or during `setUpClass()` if you have a way to undo
   loading them
 - `reset_sequences` no longer applies as sequences are naturally reset
 - `available_apps` could potentially be useful for skipping certain apps tables when using `mysqldump`
 - `serialized_rollback` no longer applies as rollback is naturally applied when reverting back to the test DB

```python
class CloneDbTestCase(TransactionTestCase):

    # Use this approach if you have a way to remove fixtures
    # @classmethod
    # def setUpClass(cls):
    #     super().setUpClass()
    #     if cls.fixtures:
    #         for db_name in cls._databases_names(include_mirrors=False):
    #             call_command(
    #                 "loaddata",
    #                 *cls.fixtures,
    #                 verbosity=0,
    #                 database=db_name,
    #             )

    def _pre_setup(self):
        super()._pre_setup()
        for db_name in self._databases_names(include_mirrors=False):  # ?
            conn = connections[db_name]
            self.test_database_name = conn.settings_dict["NAME"]

            # SQLite in-memory requires manual cloning as Django does things a little differently
            if DatabaseCreation.is_in_memory_db(self.test_database_name):
                components = urllib.parse.urlparse(self.test_database_name)
                sandbox_uri = urllib.parse.urlunparse(
                    components._replace(path=f"{components.path}_sandbox")
                )
                source = sqlite3.connect(self.test_database_name, uri=True)
                target = sqlite3.connect(sandbox_uri, uri=True)
                source.backup(target)
                source.close()
                conn.settings_dict["NAME"] = sandbox_uri
                conn.close()
                conn.connect()  # reconnect before closing so we don't lose the db
                target.close()

            else:
                conn.creation.clone_test_db(suffix="sandbox")
                conn.settings_dict = conn.creation.get_test_db_clone_settings(
                    suffix="sandbox"
                )
                conn.close()  # required for MySQL

            if self.fixtures:
                call_command(
                    "loaddata",
                    *self.fixtures,
                    verbosity=0,
                    database=db_name,
                )

    def _post_teardown(self):
        super()._post_teardown()
        for db_name in self._databases_names(include_mirrors=False):  # ?
            conn = connections[db_name]
            conn.creation.destroy_test_db(old_database_name=self.test_database_name)
            conn.close()

    def _fixture_setup(self):
        # skip everything else TransactionTestCase does:
        #  ✗ skip reset sequences
        #  ✗ skipserialised rollback
        #  ✗ load fixtures in _pre_setup()
        pass
```


Speed Comparison
----------------

Loading the database with 100,000 domains and running the tests in [tests.py](./tests.py) (with assertions removed) we
can compare the speed of `CloneDbTestCase`, `TransactionTestCase` and `TransactionTestCase` with
`serialized_rollback = True`:

```
|-------------------+-----------------+---------------------+----------------------------------------------|
| 100,000 domains   | CloneDbTestCase | TransactionTestCase | TransactionTestCase with serialized_rollback |
|-------------------+-----------------+---------------------+----------------------------------------------|
| sqlite            | 2.00s           | 1.96s               | 38.51s                                       |
|                   | 2.01s           | 1.89s               | 40.681                                       |
|                   | 2.02s           | 2.00s               | 42.14s                                       |
| postgres          | 2.23s           | 2.13s               | 44.44s                                       |
|                   | 2.22s           | 2.17s               | 45.38s                                       |
|                   | 2.17s           | 2.16s               | 44.08s                                       |
| mysql             | 2.35s           | 2.14s               | 47.00s                                       |
|                   | 2.35s           | 2.13s               | 48.13s                                       |
|                   | 2.32s           | 2.15s               | 47.62s                                       |
|-------------------+-----------------+---------------------+----------------------------------------------|
```
