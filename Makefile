.PHONY: setup test run seed clean lint

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup:
	python3.10 -m venv $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ -v --cov=src/pfm --cov-report=term-missing --cov-report=html

run:
	$(PYTHON) -m streamlit run app/main.py

seed:
	$(PYTHON) scripts/seed_data.py

clean:
	rm -rf $(VENV) .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

lint:
	$(PYTHON) -m py_compile src/pfm/**/*.py 2>/dev/null || true
