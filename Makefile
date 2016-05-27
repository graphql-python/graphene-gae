ifndef GOOGLE_APPENGINE
	export GOOGLE_APPENGINE:=/usr/local/google_appengine
endif

export PATH:=$(PATH):$(GOOGLE_APPENGINE)
export PYTHONPATH:=$(PYTHONPATH):${GOOGLE_APPENGINE}

.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

.venv:
	if [ ! -e ".venv/bin/activate_this.py" ] ; then virtualenv --clear .venv ; fi

deps: .venv
	PYTHONPATH=.venv ; . .venv/bin/activate && .venv/bin/pip install -U -r requirements.txt

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -rf {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && flake8 graphene_gae tests

test:
	PYTHONPATH=$PYTHONPATH:.venv:. . .venv/bin/activate && python setup.py test

test-all:
	PYTHONPATH=$PYTHONPATH:.venv:. . .venv/bin/activate && tox

coverage:
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && coverage run --source graphene_gae setup.py test
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && coverage report -m
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && coverage html

docs:
	rm -f docs/graphene_gae.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ graphene_gae
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && python setup.py sdist upload
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && python setup.py bdist_wheel upload

dist: clean
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && python setup.py sdist
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && python setup.py bdist_wheel
	ls -l dist

install: clean
	PYTHONPATH=$PYTHONPATH:.venv:. ; . .venv/bin/activate && python setup.py install
