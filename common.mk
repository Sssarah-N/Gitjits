# common make vars and targets:
export LINTER = flake8
export PYLINTFLAGS = --exclude=__main__.py

export CLOUD = 0

PYTHONFILES = $(shell ls *.py)
TESTFILES = $(wildcard tests/*.py)
PYTESTFLAGS = -vv --verbose --cov-branch --cov-report term-missing --tb=short -W ignore::FutureWarning

MAIL_METHOD = api

FORCE:

tests: lint pytests

lint: $(patsubst %.py,%.pylint,$(PYTHONFILES)) lint_tests

%.pylint:
	$(LINTER) $(PYLINTFLAGS) $*.py

lint_tests:
	@if [ -d tests ] && [ -n "$$(ls tests/*.py 2>/dev/null)" ]; then \
		$(LINTER) $(PYLINTFLAGS) tests/*.py; \
	fi

pytests: FORCE
	pytest $(PYTESTFLAGS) --cov=$(PKG)

# test a python file:
%.py: FORCE
	$(LINTER) $(PYLINTFLAGS) $@
	pytest $(PYTESTFLAGS) tests/test_$*.py

nocrud:
	-rm *~
	-rm *.log
	-rm *.out
	-rm .*swp
	-rm $(TESTDIR)/*~
