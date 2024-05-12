.PHONY: tags site-packages

run:
	python manage.py runserver

tags:
	ctags -R --languages=Python .

lint:
	isort .
	black .
	flake8 .

site-packages:
	export PYTHON_VERSION=$$(python -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")'); \
	ln -sf .direnv/python-$$PYTHON_VERSION/lib/python$$PYTHON_VERSION/site-packages
