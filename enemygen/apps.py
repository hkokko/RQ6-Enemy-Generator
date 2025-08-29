from django.apps import AppConfig


class EnemygenConfig(AppConfig):
    name = 'enemygen'
    verbose_name = 'Enemy Generator'

    def ready(self):
        # Import signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Fail-soft: do not block startup if signals import fails
            pass

        # Minimal, fail-soft bootstrap: if no enemy templates exist, try to load dump.sql
        # This helps ensure the Enemies page has content on first run in development.
        try:
            import os
            import subprocess
            from django.conf import settings
            from django.db import connection
            # Defer import of EnemyTemplate until apps are ready
            from .models import EnemyTemplate

            # Quick sanity: ensure DB connection can be established; otherwise skip
            try:
                connection.ensure_connection()
            except Exception:
                return

            # If there are already templates, nothing to do
            try:
                if EnemyTemplate.objects.exists():
                    return
            except Exception:
                # If querying fails, do not attempt bootstrap
                return

            project_root = str(settings.BASE_DIR)
            dump_path = os.path.join(project_root, 'dump.sql')
            if not os.path.isfile(dump_path):
                return

            # Ensure required env for docker-based import
            db_name = os.environ.get('DB_NAME') or os.environ.get('MYSQL_DATABASE')
            root_pw = os.environ.get('MYSQL_ROOT_PASSWORD')
            if not (db_name and root_pw):
                return

            def _run(cmd, timeout=120):
                try:
                    return subprocess.run(cmd, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
                except Exception as e:
                    class P:
                        returncode = 1
                        stdout = ''
                        stderr = str(e)
                    return P()

            # Verify container is up; if not, skip quietly (we won't start it here)
            ps = _run(['docker', 'exec', 'mythras-mysql', 'sh', '-c', 'true'], timeout=10)
            if ps.returncode != 0:
                return

            # Normalize password if quoted in .env
            if ((root_pw.startswith("'") and root_pw.endswith("'")) or (root_pw.startswith('"') and root_pw.endswith('"'))):
                root_pw = root_pw[1:-1]

            # Idempotent: ensure DB/user, then upload dump
            _run(['make', 'mysql-create-user'])
            _run(['make', 'upload-dump-compat', f'ARGS=--db {db_name}'], timeout=900)
        except Exception:
            # Never block app startup due to bootstrap issues
            return
