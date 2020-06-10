.PHONY: test install clean clean-pyc clean-build

test:
	flake8 ninjin
	mypy ninjin
	pytest
	pip check

install: ## install dev dependencies
	python setup.py egg_info && \
	pip install `sed -e 's/\[.*\]//g' ninjin.egg-info/requires.txt` ;

clean: clean-build clean-pyc clean-test

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

sort:
	isort -rc -m 3 -e -fgw -q