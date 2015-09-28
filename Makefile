all:
	python setup.py sdist

upload:
	python setup.py sdist upload

clean:
	rm -rf *.egg-info build dist
	find . -name __pycache__ -type d -print0 | xargs -0 rm -r
	find . -name "*.py[co]" -print0 | xargs -0 rm
