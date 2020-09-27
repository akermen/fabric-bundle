ROOT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))
VIRTUALENV := .virtualenv
pip := $(ROOT)/$(VIRTUALENV)/bin/pip
python := $(ROOT)/$(VIRTUALENV)/bin/python
fab := $(ROOT)/$(VIRTUALENV)/bin/fab

.PHONY: virtualenv install

virtualenv:
	@test -d $(ROOT)/$(VIRTUALENV) || { virtualenv --python `which python2.7` $(VIRTUALENV); }

install: virtualenv requirements.txt
	$(info --> installing requirements.txt)
	@$(pip) install -Ur requirements.txt
