DBT := uv run dbt
DBT_FLAGS := --project-dir dbt --profiles-dir dbt

# make ingest                        -> all cities, current year up to today
# make ingest YEAR=2025              -> all cities, all of 2025
# make ingest YEAR=2026 MONTH=10 CITY=orebro
YEAR ?= $(shell date +%Y)
MONTH ?=
CITY ?=

# Extra dbt flags, e.g. make transform ARGS="--full-refresh" or ARGS="-s fct_weather_monthly"
ARGS ?=

.PHONY: help ingest transform viz

help:
	@echo "make ingest     Fetch weather into data/in   (YEAR=, MONTH=, CITY= optional)"
	@echo "make transform  dbt build: raw -> staging -> prod, writes data/out   (ARGS= optional)"
	@echo "make viz        Run the marimo notebook as an app"

ingest:
	uv run ingest_weather.py $(YEAR) $(MONTH) $(if $(CITY),--city $(CITY))

transform: dbt/dbt_packages
	$(DBT) build $(DBT_FLAGS) $(ARGS)

viz:
	uv run marimo run notebooks/weather.py

# Install dbt packages (dbt_utils) once, and again whenever packages.yml changes.
dbt/dbt_packages: dbt/packages.yml
	$(DBT) deps $(DBT_FLAGS)
	@touch $@
