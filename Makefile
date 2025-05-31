.PHONY: setup format lint type-check test clean docs

# Install dependencies and set up development environment
setup:
	python3 -m venv env
	source env/bin/activate
	pip install -U pip
	pip install -r requirements.txt

# Format code using ruff
format:
	ruff format .
	ruff check --fix .

# Run linting
lint:
	ruff check .

# Run type checking
type-check:
	mypy src tests scripts

# Run tests with coverage
test:
	pytest --cov=src --cov-report=term-missing

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type d -name "build" -exec rm -r {} +
	find . -type d -name "dist" -exec rm -r {} +

# Build documentation
docs:
	mkdocs build

# Run all checks
check: format lint type-check test

# Install pre-commit hook
install-hooks:
	echo '#!/bin/sh\nmake check' > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit 