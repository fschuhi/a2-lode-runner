# --- Variables ---
ROOT_DIR := $(CURDIR)
VENV_DIR = $(ROOT_DIR)/.venv
VENV_ACTIVATE = $(VENV_DIR)/bin/activate
ACTIVATE = . $(VENV_ACTIVATE)
PIP = $(ACTIVATE) && pip
RUN_WITH_PATH = $(ACTIVATE) && PYTHONPATH=$(ROOT_DIR)
RESEARCH_DIR = $(ROOT_DIR)/research

# The sentinel file to check if setup is complete
SETUP_STAMP = $(VENV_DIR)/.setup_stamp

# --- Phony targets ---
.PHONY: all setup test test-verbose nwchapter nwindex nwchunk latex-to-md nwhtml clean showtree gentree filesdump filesdump-detailed help

# Default target runs 'setup'
all: setup

# --- Virtual Environment Setup ---
$(VENV_DIR)/bin/activate:
	python3 -m venv $(VENV_DIR)

# Smart 'setup' target
$(SETUP_STAMP): $(VENV_DIR)/bin/activate requirements.txt
	@echo "--- Installing dependencies ---"
	$(PIP) install -r requirements.txt
	@echo "--- Setup complete ---"
	@touch $(SETUP_STAMP)

setup: $(SETUP_STAMP) ## Create venv and install dependencies

# --- Testing Targets ---
test: $(SETUP_STAMP) ## Run all tests (quiet mode)
	$(RUN_WITH_PATH) pytest -q

test-verbose: $(SETUP_STAMP) ## Run tests with verbose output
	$(RUN_WITH_PATH) pytest -v -s

# --- noweb targets ---
nwchapter: $(SETUP_STAMP) ## export one main.nw chapter as compact woven Markdown
	@test -n "$(CHAPTER)" || (echo "Usage: make nwchapter CHAPTER=6" && exit 1)
	$(RUN_WITH_PATH) python scripts/nwtool.py chapter $(CHAPTER) --nw reference/lode_runner_reveng/main.nw -o tmp/main-chapter-$(CHAPTER).md

nwindex: $(SETUP_STAMP) ## export the whole main.nw chapter/chunk/identifier index
	$(RUN_WITH_PATH) python scripts/nwtool.py index --nw reference/lode_runner_reveng/main.nw

nwchunk: $(SETUP_STAMP) ## export one named main.nw chunk (continuations + one-level references)
	@test -n "$(NAME)" || (echo 'Usage: make nwchunk NAME="level draw routine"' && exit 1)
	$(RUN_WITH_PATH) python scripts/nwtool.py chunk "$(NAME)" --nw reference/lode_runner_reveng/main.nw $(if $(MAXLINES),--max-lines $(MAXLINES),)

latex-to-md: $(SETUP_STAMP) ## convert LaTeX main.nw to markdown (called only once)
	$(RUN_WITH_PATH) python scripts/latex_to_md.py \
		$(ROOT_DIR)/reference/lode_runner_reveng/main.nw \
		$(RESEARCH_DIR)/main.nw.md

nwhtml: $(SETUP_STAMP) ## convert main.nw-edited.md to html (call after editing)
	$(RUN_WITH_PATH) python scripts/weave_html.py \
		$(RESEARCH_DIR)/main.nw-edited.md \
		$(RESEARCH_DIR)/build

# --- Utility Targets ---

filesdump: $(SETUP_STAMP) gentree ## Create context dump for LLMs
	@if [ -f manifest.lst ]; then \
		$(RUN_WITH_PATH) python tools/concat_files.py manifest.lst > tmp/filesdump.txt; \
		echo "Generated tmp/filesdump.txt"; \
	else \
		echo "Error: manifest.lst not found"; \
	fi

filesdump-detailed: $(SETUP_STAMP) gentree ## Create context dump for LLMs with per-file size details
	@if [ -f manifest.lst ]; then \
		$(RUN_WITH_PATH) python tools/concat_files.py --detailed --sort manifest.lst > tmp/filesdump.txt; \
		echo "Generated tmp/filesdump.txt"; \
	else \
		echo "Error: manifest.lst not found"; \
	fi

clean: ## Remove venv, cache, and tmp files
	rm -rf $(VENV_DIR) .pytest_cache tmp
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.egg-info" -type d -prune -exec rm -rf {} +

showtree: ## Show project directory structure
	tree -I ".venv|__pycache__|.idea|.pytest_cache|*egg-info|tmp"

gentree: ## Save tree structure to file
	mkdir -p tmp
	tree -I ".venv|__pycache__|.idea|.pytest_cache|*egg-info|tmp" > tmp/project_tree.txt

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
