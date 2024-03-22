import sqlite3
import urllib

import pytest
from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase

from .models import DomainWhitelist

pytestmark = pytest.mark.django_db


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
        for db_name in self._databases_names(include_mirrors=False):
            conn = connections[db_name]
            self.test_database_name = conn.settings_dict["NAME"]

            # SQLite in-memory requires manual cloning as Django does things a little differently
            if conn.vendor == "sqlite" and conn.is_in_memory_db():
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
        for db_name in self._databases_names(include_mirrors=False):
            conn = connections[db_name]
            conn.creation.destroy_test_db(old_database_name=self.test_database_name)
            conn.close()

    def _fixture_setup(self):
        # skip everything else TransactionTestCase does:
        #  ✗ skip reset sequences
        #  ✗ skipserialised rollback
        #  ✗ load fixtures in _pre_setup()
        pass


class DomainWhitelistTestCase(CloneDbTestCase):
    fixtures = ["fixture.json"]

    def test_first(self):
        DomainWhitelist.objects.create(domain="google.com")
        self.assertQuerySetEqual(
            DomainWhitelist.objects.values_list("domain", flat=True).order_by("domain"),
            [
                "djangoproject.com",  # from migrations
                "google.com",  # from this test
                "python.org",  # from fixture
            ],
        )

    def test_second(self):
        """
        This test will fail if the class is a subclass of TransactionTestCase
        """
        self.assertQuerySetEqual(
            DomainWhitelist.objects.values_list("domain", flat=True).order_by("domain"),
            [
                "djangoproject.com",  # from migrations
                "python.org",  # from fixture
            ],
        )


class DomainWhitelistNoFixtureTestCase(CloneDbTestCase):
    """
    Fixture from the test case class above should not affect this.
    """

    def test_only_from_migrations(self):
        self.assertQuerySetEqual(
            DomainWhitelist.objects.values_list("domain", flat=True).order_by("domain"),
            [
                "djangoproject.com",  # from migrations
            ],
        )
