.PHONY: build test test-verbose test-coverage format lint validate help run

PYTHON = python3
PIP = pip

build:
	$(PYTHON) -m py_compile main.py

test:
	$(PYTHON) -m pytest . -v

test-coverage:
	$(PYTHON) -m pytest . --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=60

format:
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

lint:
	flake8 --max-line-length=88 --exclude=.venv .
	mypy --ignore-missing-imports --disable-error-code=arg-type --disable-error-code=attr-defined .

validate: build format lint test-coverage
	@echo "✅ Validation complete"

run:
	$(PYTHON) main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
