# Suspend command echo for non-verbose builds
ifeq ("$(VERBOSE)","1")
NO_ECHO :=
TEST_VERBOSE := -v
else
NO_ECHO := @
TEST_VERBOSE :=
endif

# Set up project-relative source paths
BUILD_OUTPUTS     := $(abspath ./dist) $(abspath ./build) $(abspath ./blatann.egg-info)

TEST_ROOT := $(abspath ./tests)
TEST_VERBOSE := -v

# Utility commands
RM    := rm -rf
CD    := cd
CP    := cp
TOUCH := touch
MKDIR := mkdir
CAT   := cat

ifeq ($(OS),Windows_NT)
PYTHON   ?= python
else
PYTHON   ?= python3
endif

# Python-based commands
PIP      := $(PYTHON) -m pip
VENV     := $(PYTHON) -m venv
COVERAGE := $(PYTHON) -m coverage
RUFF     := $(PYTHON) -m ruff
ISORT    := $(PYTHON) -m isort

# Target Definitions

.PHONY: default binaries clean run-tests setup-dev lint-check format

# First target, default to building the wheel
default: binaries

binaries:
	$(NO_ECHO)$(PYTHON) -m build

clean:
	$(NO_ECHO)$(RM) $(BUILD_OUTPUTS)

setup-dev:
	$(NO_ECHO)$(PIP) install -e .[dev]

run-tests:
	$(NO_ECHO)$(PYTHON) -m unittest discover $(TEST_VERBOSE) -s $(TEST_ROOT) -t $(TEST_ROOT)

lint-check:
	$(NO_ECHO)$(RUFF) check .
	$(NO_ECHO)$(ISORT) --check .

format:
	$(NO_ECHO)$(RUFF) check --fix .
	$(NO_ECHO)$(ISORT) .
