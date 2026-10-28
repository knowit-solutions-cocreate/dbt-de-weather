# Loads .env (WEATHER_DATA_DIR, see .env.example) into every uv run, also after cd dbt.
# Also read here, for the paths make cleanup deletes.
ifneq ($(wildcard .env),)
include .env
export UV_ENV_FILE := $(CURDIR)/.env
endif
DATA_DIR := $(or $(WEATHER_DATA_DIR),data)
DB_PATH := $(or $(WEATHER_DB_PATH),weather.duckdb)

# dbt runs from dbt/, where profiles.yml lives (and its fallback paths are relative to).
DBT := cd dbt && uv run dbt

# Extra dbt flags, e.g. make transform ARGS="--full-refresh" or ARGS="-s fct_weather_monthly"
ARGS ?=

.PHONY: help ingest transform docs viz orchestrate cleanup

help:
	@echo "make ingest     Fetch weather into data/in   (YEAR=, MONTH=, CITY= optional)"
	@echo "make transform  dbt build: staging -> prod, writes data/out   (ARGS= optional)"
	@echo "make docs       Generate and serve the dbt docs   -> http://localhost:8080"
	@echo "make viz        Run the marimo notebook as an app"
	@echo "make cleanup    Delete the Dagster instance, weather.duckdb and everything in data/in and data/out"

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

# Keeps the .gitkeep files, which data/in and data/out need to exist.
cleanup:
	rm -rf .dagster $(DB_PATH) $(DB_PATH).wal
	find $(DATA_DIR)/in $(DATA_DIR)/out -mindepth 1 ! -name .gitkeep -delete

# Install dbt packages (dbt_utils) once, and again whenever packages.yml changes.
dbt/dbt_packages: dbt/packages.yml
	$(DBT) deps
	@touch $@
