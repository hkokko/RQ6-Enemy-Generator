import pathlib
from typing import List
import pytest

# Ensure any tests under enemygen/tests/ run last across the whole test session.
# We implement pytest_collection_modifyitems to move any tests collected from
# enemygen/tests/** to the end of the item list, preserving relative order of all other tests.
# This is a minimal, plugin-free approach.

def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: List[pytest.Item]):
    tail: List[pytest.Item] = []
    head: List[pytest.Item] = []
    for it in items:
        # nodeid typically looks like 'enemygen/tests/file.py::TestName::test_func'
        node_path = it.nodeid.split('::', 1)[0]
        # Normalize to forward slashes for safety
        norm = node_path.replace('\\', '/')
        if norm.startswith('enemygen/tests/'):
            tail.append(it)
        else:
            head.append(it)
    if tail:
        items[:] = head + tail



# --- Pre-test DB ensure: create DB and import dump.sql if needed ---
# This fixture ensures that before any tests run, the MySQL database defined in .env
# exists and contains tables imported from dump.sql. It leverages the existing
# Makefile targets and docker-based upload script. It intentionally runs after
# pytest-django initialized Django but before DB-using tests, and uses
# django_db_blocker to safely access the DB.
import os
import subprocess


#@pytest.fixture(scope="session", autouse=True)
@pytest.fixture(scope="session", autouse=True)
def ensure_db_and_dump_loaded(django_db_setup, django_db_blocker):
    """
    Ensure the MySQL database exists and dump.sql is imported before tests start.

    Behavior:
    - Reads .env through settings (already loaded) and environment for DB_* and MYSQL_ROOT_PASSWORD.
    - Verifies docker container 'mythras-mysql' is running; if not, emits a clear message.
    - Creates DB/user via `make mysql-create-user` if DB missing.
    - If DB has no expected tables, attempts `make upload-dump-compat` once.
    - Soft-fails (skip) with clear diagnostics if prerequisites are missing, unless FORCE_VERIFY_DUMP=1
      in which case it fails hard.
    """
    from django.conf import settings as dj_settings

    def _run(cmd, cwd=None):
        try:
            p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return p.returncode, p.stdout, p.stderr
        except FileNotFoundError as e:
            return 127, '', str(e)

    # Gather configuration
    project_root = os.path.abspath(os.path.dirname(__file__))
    db_name = os.environ.get('DB_NAME') or getattr(dj_settings, 'DATABASES', {}).get('default', {}).get('NAME')
    db_user = os.environ.get('DB_USER') or os.environ.get('MYSQL_USER') or 'mythras_eg'
    db_password = os.environ.get('DB_PASSWORD') or os.environ.get('MYSQL_PASSWORD') or ''
    root_pw = os.environ.get('MYSQL_ROOT_PASSWORD')
    dump_path = os.path.join(project_root, 'dump.sql')
    force = os.environ.get('FORCE_VERIFY_DUMP', '0') == '1'

    # Quick exits: if critical env not present, do nothing (non-fatal unless force)
    missing = []
    if not db_name:
        missing.append('DB_NAME')
    if not root_pw:
        missing.append('MYSQL_ROOT_PASSWORD')

    if missing:
        msg = f"Missing required env for DB bootstrap: {', '.join(missing)}."
        if force:
            pytest.fail(msg)
        else:
            pytest.skip(msg)

    # Verify container is running
    code, out, err = _run(['docker', 'exec', 'mythras-mysql', 'sh', '-c', 'true'])
    if code != 0:
        # Try to show ps output for context
        _c, clist, _e = _run(['docker', 'ps', '-a'])
        clist_tail = '\n'.join((clist or '').splitlines()[-5:])
        msg = "MySQL container 'mythras-mysql' is not running. Run 'make start-db' first.\n" \
              f"[docker ps -a] tail:\n{clist_tail}"
        if force:
            pytest.fail(msg)
        else:
            pytest.skip(msg)

    # Helper to run SQL as root to check DB/tables
    def _mysql_root(sql, db=None):
        sh = f"MYSQL_PWD='{root_pw}' mysql -N -B -uroot"
        if db:
            sh += f" {db}"
        sh += f" -e {sql!r}"
        return _run(['docker', 'exec', '-i', 'mythras-mysql', 'sh', '-c', sh])

    # Check if database exists
    code, out, err = _mysql_root(f"SHOW DATABASES LIKE '{db_name}';")
    if code != 0:
        # Can't query root? Provide diagnostics but continue to try make target.
        pass
    db_exists = (out or '').strip() == db_name

    with django_db_blocker.unblock():
        # Create DB/user if missing
        if not db_exists:
            _rc, _o, _e = _run(['make', 'mysql-create-user'], cwd=project_root)
            # Re-check
            code, out, err = _mysql_root(f"SHOW DATABASES LIKE '{db_name}';")
            db_exists = (out or '').strip() == db_name

        if not db_exists:
            msg = f"Database '{db_name}' does not exist after mysql-create-user. Check MYSQL_ROOT_PASSWORD and container logs."
            if force:
                pytest.fail(msg)
            else:
                pytest.skip(msg)

        # Check if there are any tables; try some candidate tables
        def _has_tables():
            c, o, e = _mysql_root('SHOW TABLES;', db=db_name)
            return c == 0 and bool((o or '').strip())

        if not _has_tables():
            # Try to import dump if present
            if os.path.isfile(dump_path):
                _rc, _o, _e = _run(['make', 'upload-dump-compat'], cwd=project_root)
            # Re-check
            if not _has_tables():
                msg = (
                    "Database has no tables. Could not import dump automatically.\n"
                    "- Ensure dump.sql exists at project root and is valid.\n"
                    "- You can run: make upload-dump-compat\n"
                    "- Or start DB: make start-db\n"
                )
                if force:
                    pytest.fail(msg)
                else:
                    pytest.skip(msg)

# --- Safety guard: forbid destructive DROP DATABASE on the active DB during tests ---
@pytest.fixture(scope="session", autouse=True)
def forbid_drop_database(django_db_setup, django_db_blocker):
    """
    Prevent accidental DROP DATABASE operations against the configured DB during tests.
    This does not interfere with normal table-level operations or truncate/flush behavior
    that Django's TestCase/TransactionTestCase may perform. It only guards against a full
    database drop on the active database name (e.g., 'mythras_eg').
    """
    from django.conf import settings as dj_settings
    import django.db.backends.utils as dbu

    target_db = (dj_settings.DATABASES.get("default", {}).get("NAME") or "").lower()
    if not target_db:
        return

    orig_execute = dbu.CursorWrapper.execute

    def safe_execute(self, sql, params=None):
        try:
            text = sql.decode() if isinstance(sql, (bytes, bytearray)) else str(sql)
        except Exception:
            text = str(sql)
        low = text.lower()
        if "drop database" in low and target_db in low:
            raise AssertionError(f"DROP DATABASE on '{target_db}' is forbidden during tests")
        return orig_execute(self, sql, params)

    # Apply patch for the duration of the session
    dbu.CursorWrapper.execute = safe_execute
    try:
        yield
    finally:
        # Restore original execute
        dbu.CursorWrapper.execute = orig_execute

# --- Test session DB hygiene and schema compatibility helpers ---
import uuid
from django.contrib.auth import get_user_model


# Ensure a permanent manual test user exists for local manual testing.
# Requirement: At the start of the pytest run, delete any existing 'manualuser',
# then create or update it with password 'spade1' and keep it permanently.
@pytest.fixture(scope="session", autouse=True)
def ensure_contenttypes_schema_compat(django_db_setup, django_db_blocker):
    # Also monkeypatch Django's create_contenttypes to ensure the schema relax is applied
    # right before content types are created during flush/post_migrate.
    """
    Some legacy databases (e.g., those imported from older Django) still have
    a non-null, no-default 'name' column in django_content_type.
    Django 3.2 no longer uses that column and inserts only (app_label, model),
    which causes MySQL (STRICT) to error with:
      OperationalError (1364): Field 'name' doesn't have a default value
    To be compatible, relax the 'name' column to allow NULL default if it exists.
    """
    from django.db import connection
    import django.contrib.contenttypes.management as ct_mgmt
    import django.contrib.auth.management as auth_mgmt

    def _relax_contenttypes_name():
        with django_db_blocker.unblock():
            try:
                with connection.cursor() as cur:
                    # Check if the 'name' column exists on django_content_type
                    cur.execute(
                        """
                        SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'django_content_type'
                          AND COLUMN_NAME = 'name'
                        """
                    )
                    row = cur.fetchone()
                    if row:
                        # Column exists; relax it to be NULLable with a benign default.
                        # Use the current column type from information_schema for safety.
                        cur.execute(
                            """
                            SELECT COLUMN_TYPE FROM information_schema.COLUMNS
                            WHERE TABLE_SCHEMA = DATABASE()
                              AND TABLE_NAME = 'django_content_type'
                              AND COLUMN_NAME = 'name'
                            """
                        )
                        type_row = cur.fetchone()
                        col_type = type_row[0] if type_row and type_row[0] else 'VARCHAR(255)'
                        try:
                            cur.execute(f"ALTER TABLE django_content_type MODIFY COLUMN name {col_type} NULL DEFAULT ''")
                        except Exception:
                            pass
            except Exception:
                # Silent fallback; tests will still reveal issues if present
                pass

    # Apply at session start as a baseline
    _relax_contenttypes_name()

    # Monkeypatch create_contenttypes so any invocation during flush/post_migrate
    # first ensures the relaxed schema is in place.
    _orig_create_contenttypes = ct_mgmt.create_contenttypes

    def _patched_create_contenttypes(*args, **kwargs):
        _relax_contenttypes_name()
        return _orig_create_contenttypes(*args, **kwargs)

    # Patch both the original module and the alias imported by auth.management
    try:
        ct_mgmt.create_contenttypes = _patched_create_contenttypes
        auth_mgmt.create_contenttypes = _patched_create_contenttypes
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def ensure_manualuser(django_db_setup, django_db_blocker):
    """
    Session-start hook to reset and ensure a permanent manual user for manual testing.
    We carefully establish a DB connection and use a short autocommit context to avoid
    interfering with pytest-django's transactional setup.
    """
    from django.db import connection, transaction

    with django_db_blocker.unblock():
        try:
            # 1) Ensure connection is established and healthy
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            # If even a simple SELECT fails, don't crash the suite here; DB tests will report.
            return

        User = get_user_model()
        try:
            # 2) Force autocommit during this short maintenance window to avoid
            # interfering with pytest-django transactional test setup.
            prev_autocommit = connection.get_autocommit()
            try:
                connection.set_autocommit(True)
                # Delete any prior manualuser
                User.objects.filter(username="manualuser").delete()
                # Create or update
                user, _created = User.objects.get_or_create(
                    username="manualuser",
                    defaults={
                        "email": "manualuser@example.com",
                        "is_active": True,
                    },
                )
                user.is_active = True
                user.set_password("spade1")
                user.save()
            finally:
                # Restore original autocommit state
                try:
                    connection.set_autocommit(prev_autocommit)
                except Exception:
                    pass
                # Close this maintenance connection explicitly to ensure a clean
                # connection is established later by pytest-django for tests.
                try:
                    connection.close()
                except Exception:
                    pass
        except Exception:
            # Swallow any unexpected issues to avoid breaking collection/startup.
            # Actual DB-dependent tests will surface concrete failures.
            return


@pytest.fixture()
def localtest_username() -> str:
    """
    Provide a unique username starting with 'localtest-' for each test invocation.
    Example: localtest-<10-hex-chars>
    """
    return f"localtest-{uuid.uuid4().hex[:10]}"


# --- Post-test DB ensure: keep database available after pytest session ---
# Guarantee that immediately after pytest, the named database exists so `make mysql-shell`
# works without ERROR 1049. This is non-destructive and only creates DB/user if missing.
import os as _os
import subprocess as _subprocess
import pytest as _pytest

@_pytest.fixture(scope="session", autouse=True)
def ensure_db_exists_after_tests():
    # Defer imports to avoid early Django initialization side effects
    from django.conf import settings as _dj_settings

    def _run(cmd, cwd=None):
        try:
            p = _subprocess.run(cmd, cwd=cwd, stdout=_subprocess.PIPE, stderr=_subprocess.PIPE, text=True)
            return p.returncode, p.stdout, p.stderr
        except FileNotFoundError as e:
            return 127, '', str(e)

    project_root = _os.path.abspath(_os.path.dirname(__file__))

    # Make sure we operate on the same DB name the app uses
    db_name = _os.environ.get('DB_NAME') or _dj_settings.DATABASES.get('default', {}).get('NAME')
    root_pw = _os.environ.get('MYSQL_ROOT_PASSWORD')

    # Yield to run entire test session first; finalizer logic runs after all tests
    yield

    # Best-effort: if essentials missing, try to load from .env at project root
    if not (db_name and root_pw):
        env_path = _os.path.join(project_root, '.env')
        if _os.path.isfile(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip()
                        # strip surrounding quotes if any
                        if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                            v = v[1:-1]
                        if k == 'DB_NAME' and not db_name:
                            db_name = v
                        elif k == 'MYSQL_ROOT_PASSWORD' and not root_pw:
                            root_pw = v
                        elif k == 'MYSQL_DATABASE' and not db_name:
                            db_name = v
            except Exception:
                pass

    # If we still lack essentials, do nothing (non-fatal)
    if not db_name or not root_pw:
        return

    # Ensure container is up; if not, try to start it without destroying data
    code, _, _ = _run(['docker', 'exec', 'mythras-mysql', 'sh', '-c', 'true'])
    if code != 0:
        # Check if container exists (stopped)
        _c1, out1, _e1 = _run(['docker', 'ps', '-a', '--filter', 'name=mythras-mysql', '--format', '{{.Names}}'])
        exists = (_c1 == 0) and bool((out1 or '').strip())
        if exists:
            # Non-destructive start of existing container
            _c2, _o2, _e2 = _run(['docker', 'start', 'mythras-mysql'])
            # Retry a few times for readiness
            for _ in range(10):
                code, _, _ = _run(['docker', 'exec', 'mythras-mysql', 'sh', '-c', 'true'])
                if code == 0:
                    break
        else:
            # Container absent: run a new one without removing any existing containers
            # Pull minimal config from env/.env
            host_ip = _os.environ.get('DB_HOST', '127.0.0.1') or '127.0.0.1'
            host_port = str(_os.environ.get('DB_PORT', '3308') or '3308')
            image = _os.environ.get('MYSQL_IMAGE', 'docker.io/library/mysql:8') or 'docker.io/library/mysql:8'
            # Run container; do not call any make target that might rm -f
            _run(['docker', 'run', '--name', 'mythras-mysql', '-p', f'{host_ip}:{host_port}:3306', '-e', f'MYSQL_ROOT_PASSWORD={root_pw}', '-d', image])
            # Wait for readiness
            for _ in range(10):
                code, _, _ = _run(['docker', 'exec', 'mythras-mysql', 'sh', '-c', 'true'])
                if code == 0:
                    break
        if code != 0:
            return  # give up silently

    def _mysql_root(sql, db=None):
        sh = f"MYSQL_PWD='{root_pw}' mysql -N -B -uroot"
        if db:
            sh += f" {db}"
        sh += f" -e {sql!r}"
        return _run(['docker', 'exec', '-i', 'mythras-mysql', 'sh', '-c', sh])

    # Check existence and create if missing (idempotent)
    c, out, _ = _mysql_root(f"SHOW DATABASES LIKE '{db_name}';")
    db_exists = (c == 0) and ((out or '').strip() == db_name)
    if not db_exists:
        _run(['make', 'mysql-create-user'], cwd=project_root)
        # Re-check once
        c, out, _ = _mysql_root(f"SHOW DATABASES LIKE '{db_name}';")
        # No assert: we keep this silent to not affect test results post hoc
        _ = (c == 0) and ((out or '').strip() == db_name)
