# Minimal makefile for Sphinx documentation
#

RM := rm

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build
PYTHON_SOURCE = ../blatann

.PHONY: help Makefile all apidoc

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

all: apidoc
	@$(MAKE) --no-print-directory html

clean-apidoc:
	@$(RM) -rf $(SOURCEDIR)/blatann.*.rst

apidoc: clean-apidoc
	@sphinx-apidoc -e -M -o $(SOURCEDIR) $(PYTHON_SOURCE)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
