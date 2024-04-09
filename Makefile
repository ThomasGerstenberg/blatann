# Suspend command echo for non-verbose builds
ifeq ("$(VERBOSE)","1")
NO_ECHO :=
else
NO_ECHO := @
endif

# Set up project-relative source paths
BUILD_OUTPUTS     := $(abspath ./dist) $(abspath ./build) $(abspath ./blatann.egg-info)

TEST_ROOT := $(abspath ./tests)
TEST_VERBOSE := -v

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
	$(PYTHON) -m build

clean:
	$(RM) $(BUILD_OUTPUTS)

setup-dev:
	$(PIP) install -e .[dev]

run-tests:
	$(PYTHON) -m unittest discover $(TEST_VERBOSE) -s $(TEST_ROOT) -t $(TEST_ROOT)
