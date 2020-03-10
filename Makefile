# Suspend command echo for non-verbose builds
ifeq ("$(VERBOSE)","1")
NO_ECHO :=
else
NO_ECHO := @
endif

# Set up project-relative source paths
BUILD_PATH        := $(abspath ./build_tools)
BUILD_OUTPUTS     := $(abspath ./dist) $(abspath ./build)
SETUP_SCRIPT      := $(abspath ./setup.py)

TEST_ROOT := $(abspath ./tests)
TEST_VERBOSE := -v
REQUIREMENTS = requirements.txt

# Utility commands
RM       := $(NO_ECHO)rm -rf
CD       := $(NO_ECHO)cd
CP       := $(NO_ECHO)cp
TOUCH    := $(NO_ECHO)touch
AWK      := $(NO_ECHO)gawk
MKDIR    := $(NO_ECHO)mkdir
CAT      := $(NO_ECHO)cat

# Python-based commands
PYTHON   := $(NO_ECHO)python3
PIP      := $(PYTHON) -m pip
VENV     := $(PYTHON) -m virtualenv
COVERAGE := $(PYTHON) -m coverage

# Target Definitions

.PHONY: all binaries clean run-tests setup-dev

all: binaries

binaries:
	$(PYTHON) setup.py bdist_wheel sdist

clean:
	$(RM) $(BUILD_OUTPUTS)

setup-dev:
	$(PIP) install -r $(REQUIREMENTS)

run-tests:
	$(PYTHON) -m unittest discover $(TEST_VERBOSE) -s $(TEST_ROOT) -t $(TEST_ROOT)
