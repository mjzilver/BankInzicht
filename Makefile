SRC_DIR := src
TEST_DIR := tests
ENTRY := $(SRC_DIR)/app.py
VENV_DIR := venv
PYTHON := python3
PY := $(VENV_DIR)/bin/python
PIP := $(PYTHON) -m pip

.PHONY: install run format lint clean test

all: run

$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)
	$(PY) -m pip install -U pip

install: $(VENV_DIR)
	$(PY) -m pip install -e .

run: install
	$(PY) $(ENTRY)

test: install
	$(PY) -m pytest -q

format:
	black $(SRC_DIR) $(TEST_DIR)

lint:
	ruff check $(SRC_DIR) $(TEST_DIR)

lint-fix:
	ruff check --fix $(SRC_DIR) $(TEST_DIR)

clean:
	rm -rf $(VENV_DIR)
