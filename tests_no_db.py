from django.test.runner import DiscoverRunner
from django.db import connections
from django.db.utils import OperationalError

class NoCreateDBTestRunner(DiscoverRunner):
    """
    A test runner that does NOT create or destroy the test database.
    It simply verifies that the configured database exists and is reachable.
    This is useful when tests are expected to run against an already provisioned
    database (e.g., a shared or preloaded schema) and we must not attempt to
    create/drop it.
    """

    def setup_databases(self, **kwargs):
        # Ensure the default connection can connect; do not create DBs.
        alias = "default"
        conn = connections[alias]
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except OperationalError as exc:
            raise RuntimeError(
                "Test database is not available. The runner is configured to not "
                "create or delete databases. Ensure the configured database exists "
                f"and is reachable. Original error: {exc}"
            )
        # Return an empty list indicating no databases were set up
        return []

    def teardown_databases(self, old_config, **kwargs):
        # Do nothing; do not attempt to destroy any databases
        return None
