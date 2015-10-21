all: sdist

init:
	virtualenv -p python3 .env
	.env/bin/pip install -f https://cdn.research.pdx.edu/pypi/dist/ -e .[dev]
	$(MAKE) test

test:
	.env/bin/python runtests.py

sdist:
	rm -rf dist
	python setup.py sdist

upload: sdist
	scp dist/django-arcutils* hrimfaxi:/vol/www/cdn/pypi/dist

clean:
	rm -rf *.egg-info build dist
	find . -name __pycache__ -type d -print0 | xargs -0 rm -r
	find . -name "*.py[co]" -print0 | xargs -0 rm
