Additional Code Formatters
==========================

May 2024


Django runs `black` on generated code with its utility function `run_formatters()`. There are a couple of ways we can
inject additional formatters, for eg [isort](https://github.com/PyCQA/isort).


Shim Black
----------

A simple way to do this is to shim the command `black` with a shell script that delegates processing to other
formatters:

```sh
#!/bin/sh

# Django runs the command `black --fast -- <list-of-files>`

# Call original black with same arguments supplied
python -m black $*

# Additionally call isort
isort "${*:3}"
```

This means you need the above to be called `black` and on your `$PATH` when generating migrations, which may be
undesirable.


Monkey Patch
------------

Alternatively we can wrap & monkey patch `run_formatters()` to supplement its behaviour. For eg we can place this in
a suitable location like an app's config:

```python
import django.core.management.utils
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
            [isort_path, *written_files],
            capture_output=True,
        )

django.core.management.utils.run_formatters = run_formatters_extended
```
