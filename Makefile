distribution = django-arcutils
egg_name = django_arcutils
egg_info = $(egg_name).egg-info
package = arcutils
sdist = dist/$(distribution)-$(version).tar.gz
upload_path = hrimfaxi:/vol/www/cdn/pypi/dist
venv = .env
python_version ?= python3.3
version = $(shell cat VERSION)

sources = $(shell find . \
    -not -path '.' \
    -not -path '*/\.*' \
    -not -path './build' -not -path './build/*' \
    -not -path './dist' -not -path './dist/*' \
    -not -path './*\.egg-info' -not -path './*\.egg-info/*' \
    -not -path '*/__pycache__*' \
)

init: install test
reinit: clean-venv clean-install init

venv: $(venv)
$(venv):
	virtualenv -p $(python_version) $(venv)
clean-venv:
	rm -rf $(venv)

install: venv $(egg_info)
reinstall: clean-install install
$(egg_info):
	$(venv)/bin/pip install -r requirements.txt
clean-install:
	rm -rf $(egg_info)

test: install
	$(venv)/bin/runcommand test
coverage:
	$(venv)/bin/runcommand test --with-coverage

tox: install
	$(venv)/bin/tox
tox-clean:
	rm -rf .tox
retox: tox-clean tox

sdist: $(sdist)
$(sdist): $(sources)
	python setup.py sdist
clean-sdist:
	rm -f $(sdist)

upload: sdist
	scp $(sdist) $(upload_path)

upload-to-pypi: $(sdist)
	python setup.py sdist upload

clean: clean-pyc
clean-all: clean-install clean-pyc clean-sdist clean-venv
	rm -rf build dist
clean-pyc:
	find . -name __pycache__ -type d -print0 | xargs -0 rm -r

.PHONY = \
    init reinit venv install reinstall test coverage sdist upload upload-to-pypi \
    clean-venv clean-install clean-sdist \
    clean clean-all clean-pyc
