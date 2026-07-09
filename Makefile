.PHONY: setup compile test check api dashboard

PYTHON ?= python

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

compile:
	$(PYTHON) -m compileall src dashboard tests

test:
	$(PYTHON) -m pytest -q

check: compile test

api:
	uvicorn src.api.main:app --reload

dashboard:
	$(PYTHON) dashboard/build_dashboard_data.py

