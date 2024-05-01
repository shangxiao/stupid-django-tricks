import shutil
import subprocess

import django.core.management.utils
from django.apps import AppConfig

from django.core.management.utils import run_formatters


def run_formatters_extended(written_files, black_path=(sentinel := object())):
    # When wrapping run_formatters() we need to be careful to preserve calling behaviour
    if black_path is sentinel:
        run_formatters(written_files)
    else:
        run_formatters(written_files, black_path)

    # Additionally run isort
    isort_path = shutil.which("isort")
    if isort_path:
        subprocess.run(
            [isort_path, "--force-single-line-imports", *written_files],
            capture_output=True,
        )


django.core.management.utils.run_formatters = run_formatters_extended


class IsortMigrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "isort_migrations"
