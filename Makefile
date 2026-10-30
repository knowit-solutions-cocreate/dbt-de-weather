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

.PHONY: help ingest transform docs viz cleanup

help:
	@echo "make ingest     Fetch weather into data/raw   (YEAR=, MONTH=, CITY= optional)"
	@echo "make transform  dbt build: staging -> prod, writes data/prod   (ARGS= optional)"
	@echo "make docs       Generate static dbt docs   -> dbt/target/static_index.html"
	@echo "make viz        Export the marimo notebook   -> data/report/weather.html"
	@echo "make cleanup    Delete the parquet files in data/raw, data/stg, data/prod and weather.duckdb"

ingest:
	uv run ingest_weather.py $(YEAR) $(MONTH) $(if $(CITY),--city $(CITY))

transform: dbt/dbt_packages
	$(DBT) build $(DBT_FLAGS) $(ARGS)

docs: dbt/dbt_packages
	$(DBT) docs generate --static $(DBT_FLAGS)
	@echo "Open dbt/target/static_index.html in a browser"

viz:
	uv run marimo export html notebooks/weather.py -o data/report/weather.html --no-include-code

# Keeps the folders and their .gitkeep (the * glob skips dotfiles).
cleanup:
	rm -rf data/raw/* data/stg/* data/prod/* weather.duckdb*

# Install dbt packages (dbt_utils) once, and again whenever packages.yml changes.
dbt/dbt_packages: dbt/packages.yml
	$(DBT) deps $(DBT_FLAGS)
	@touch $@
