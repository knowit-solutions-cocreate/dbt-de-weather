# dbt runs from dbt/, where its paths (../weather.duckdb, ../data) and profiles.yml are relative to.
DBT := cd dbt && uv run dbt

# Extra dbt flags, e.g. make transform ARGS="--full-refresh" or ARGS="-s fct_weather_monthly"
ARGS ?=

.PHONY: help orchestrate transform viz

help:
	@echo "make orchestrate  Dagster UI: ingestion (city x month partitions), dbt and the report"
	@echo "make transform    dbt build: raw -> staging -> prod, writes data/out   (ARGS= optional)"
	@echo "make viz          Run the marimo notebook as an app"

transform: dbt/dbt_packages
	$(DBT) build $(ARGS)

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
