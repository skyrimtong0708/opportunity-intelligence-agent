.PHONY: install test run dashboard

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

run:
	python -m opportunity_intel.cli run --all

dashboard:
	streamlit run dashboard/app.py

