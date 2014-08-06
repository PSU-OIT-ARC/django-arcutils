all:
	./setup.py sdist

upload:
	./setup.py sdist upload

clean:
	rm -rf *.egg-info dist
