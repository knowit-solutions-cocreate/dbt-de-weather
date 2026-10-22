# dbt runs from dbt/, where its paths (../weather.duckdb, ../data) and profiles.yml are relative to.
DBT := cd dbt && uv run dbt

# Extra dbt flags, e.g. make transform ARGS="--full-refresh" or ARGS="-s fct_weather_monthly"
ARGS ?=

.PHONY: help ingest transform docs viz

help:
	@echo "make ingest     Fetch weather into data/in   (YEAR=, MONTH=, CITY= optional)"
	@echo "make transform  dbt build: staging -> prod, writes data/out   (ARGS= optional)"
	@echo "make docs       Generate and serve the dbt docs   -> http://localhost:8080"
	@echo "make viz        Run the marimo notebook as an app"

ingest:
	uv run ingest_weather.py $(YEAR) $(MONTH) $(if $(CITY),--city $(CITY))

transform: dbt/dbt_packages
	$(DBT) build $(ARGS)

docs: dbt/dbt_packages
	$(DBT) docs generate $(DBT_FLAGS)
	$(DBT) docs serve $(DBT_FLAGS)

viz:
	uv run marimo run notebooks/weather.py

# Dagster UI at http://localhost:3000. DAGSTER_HOME keeps run and partition history between restarts.
orchestrate: dbt/dbt_packages
	mkdir -p .dagster
	DAGSTER_HOME=$(CURDIR)/.dagster uv run dagster dev

# Install dbt packages (dbt_utils) once, and again whenever packages.yml changes.
dbt/dbt_packages: dbt/packages.yml
	$(DBT) deps
	@touch $@
