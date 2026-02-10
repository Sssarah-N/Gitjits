include common.mk

# Our directories
CITIES_DIR = cities
STATES_DIR = states
COUNTRIES_DIR = countries
PARKS_DIR = parks
API_DIR = server
DB_DIR = data
SEC_DIR = security
EXAMPLES_DIR = examples
REQ_DIR = .


FORCE:

prod: all_tests github

github: FORCE
	- git commit -a
	git push origin master

all_tests: FORCE
	cd $(API_DIR); make tests
	cd $(SEC_DIR); make tests
	cd $(CITIES_DIR); make tests
	cd $(STATES_DIR); make tests
	cd $(COUNTRIES_DIR); make tests
	cd $(EXAMPLES_DIR); make tests
	cd $(DB_DIR); make tests
	cd $(PARKS_DIR); make tests

dev_env: FORCE
	pip install -r $(REQ_DIR)/requirements-dev.txt
	@echo "You should set PYTHONPATH to: "
	@echo $(shell pwd)

prod_env: FORCE
	pip install -r $(REQ_DIR)/requirements.txt
	
docs: FORCE
	cd $(API_DIR); make docs
