PREFIX := /usr/local

# helptext: MAKEFILE HELPTEXT
# helptext:

# helptext: setup:
# helptext:
# helptext: Set up the project for development
# helptext:
# helptext:
.PHONY: setup
setup:
	@./scripts/$@

# helptext: build:
# helptext:
# helptext: Build the project
# helptext:
# helptext:
.PHONY: build
build:
	@./scripts/$@

# helptext: install:
# helptext:
# helptext: Install the project
# helptext:
# helptext:
.PHONY: install
install:
	@./scripts/$@

# helptext: clean:
# helptext:
# helptext: Clean the project
# helptext:
# helptext:
.PHONY: clean
clean:
	@./scripts/$@

# helptext: format:
# helptext:
# helptext: Format the code, tests, and anything else that needs formatting in a project
# helptext:
# helptext:
.PHONY: format
format:
	@./scripts/$@

# helptext: unittest:
# helptext:
# helptext: Run the test suit for the project
# helptext:
# helptext:
.PHONY: unittest
unittest:
	@echo ""
	@echo "====================================================================="
	@echo "Run Unit Tests"
	@echo "====================================================================="
	@echo ""
	@./scripts/$@

# helptext: coverage:
# helptext:
# helptext: Run code coverage reports
# helptext:
# helptext:
.PHONY: coverage
coverage:
	@echo ""
	@echo "====================================================================="
	@echo "Check Test Coverage"
	@echo "====================================================================="
	@echo ""
	@./scripts/$@

# helptext: lint:
# helptext:
# helptext: Static code analysis for the project
# helptext:
# helptext:
.PHONY: lint
lint:
	@echo ""
	@echo "====================================================================="
	@echo "Run Linter"
	@echo "====================================================================="
	@echo ""
	@./scripts/$@

# helptext: test:
# helptext:
# helptext: Combine unit tests, coverage reports, etc
# helptext:
# helptext:
.PHONY: test
test: setup unittest coverage lint

# helptext: security-report
# helptext:
# helptext: Search for issues with the dependencies and generate a report
# helptext:
# helptext:
.PHONY: security-report
security-report:
	@./scripts/$@

# helptext: help:
# helptext:
# helptext: View the helptext in the makefile
# helptext:
# helptext:
.PHONY: help
help:
	@grep '^# helptext:' Makefile |  sed 's/.*helptext://' | less
