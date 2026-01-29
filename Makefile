SRC_DIR := src
ENTRY := $(SRC_DIR)/app.py
VENV_DIR := venv
REQS := requirements.txt
PYTHON := python3
PIP := $(VENV_DIR)/bin/pip
PY := $(VENV_DIR)/bin/python

.PHONY: install run format clean

all: run

$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install -U pip

install: $(VENV_DIR)
	$(PIP) install -r $(REQS)

run: $(VENV_DIR) install
	$(PY) $(ENTRY)

format: $(VENV_DIR)
	find $(SRC_DIR) -name "*.py" -exec $(VENV_DIR)/bin/black {} +

clean:
	rm -rf $(VENV_DIR)
