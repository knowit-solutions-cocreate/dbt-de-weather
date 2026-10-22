# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Make targets run from the repo root via `uv` (see `Makefile`); dbt itself runs from `dbt/`:

- `make transform [ARGS="--full-refresh" | ARGS="-s <model>"]` — `dbt build` (seeds, models, data tests, unit tests)
- `make viz` — `marimo run notebooks/weather.py`; use `uv run marimo edit ...` to edit
- `make orchestrate` — `dagster dev` (UI on :3000) with `DAGSTER_HOME=.dagster`; the only way to ingest. CLI: `uv run dagster asset materialize -m orchestrator.defs --select ingest/weather_daily_files --partition "orebro|2026-10"` (or `--partition-range "goteborg|2026-09...uppsala|2026-09"`)
- Raw dbt: `cd dbt && uv run dbt <cmd>` (`profiles.yml` lives in `dbt/`)
- Unit tests only: `cd dbt && uv run dbt test --select test_type:unit`
- Lint: `uv run ruff check` / `uv run ruff format`; notebook: `uv run marimo check notebooks/weather.py`

## Architecture

Pipeline: Dagster asset `ingest/weather_daily_files` → `data/in/<city>/<YYYY-MM>.parquet` → dbt (DuckDB file `./weather.duckdb`) → `data/out/<model>.parquet` → marimo notebook.

- **Cities are defined once, in `dbt/seeds/cities.csv`.** `orchestrator/partitions.py` reads city keys and lat/lon from it. Adding a city also needs a colour in `CITY_COLORS` in the notebook.
- **Ingestion** (`OpenMeteoResource` in `orchestrator/resources.py`) validates each month with a pandera (polars) schema before writing; one file per city per month, overwritten on re-fetch. Uses the Open-Meteo *archive* API only (it covers up to today); no forecast API.
- **Adapter is `dbt-duckdb` (dbt-core 1.x), not dbt v2.** The `dbt` v2 package was removed because v2 has no `external` materialization; the two packages conflict over the `dbt` executable.
- **Layers / schemas:** `raw` (seed `cities` + incremental `raw_weather_daily`, `delete+insert` on `id`, filtered by `ingested_at`), `staging` (views), `prod` (`external` models: rebuilt in full each run and written to `data/out`; in the database they are views over those parquet files). `macros/generate_schema_name.sql` makes schema names literal (`raw`, not `main_raw`).
- **dbt paths are relative to `dbt/`** (`../weather.duckdb` and `external_root: ../data/out` in `profiles.yml`, the `../data/in` glob in `models/raw/sources.yml`), because dagster-dbt always runs dbt with `dbt/` as working directory; the Makefile does the same. Running dbt from another directory breaks them, including the stored paths in the prod views. Paths in `orchestrator/` are built from `__file__`.
- **Orchestration (Dagster)** lives in `orchestrator/`: `partitions.py` (city × month from 2024-01, month keys `YYYY-MM`; also `CITIES` with coordinates), `resources.py` (`OpenMeteoResource`, the archive API client registered as resource `open_meteo`, plus the pandera schema), `assets.py` (ingestion asset returning polars frames via `OpenMeteoResource.fetch_month`, plus `@dbt_assets` running `dbt build`, plus `report/weather_html`: `marimo export html --no-include-code` of the notebook into `data/report/weather.html`, a snapshot with the year dropdown on its default), `io_managers.py` (writes each partition to `data/in/<city>/<YYYY-MM>.parquet`; assets hand it a dict of frames keyed by partition key, since the ingestion asset has a single-run backfill policy), `jobs.py` (`weather_monthly` job plus a schedule, off by default, that fetches last month for all cities in one run and builds dbt once) and `defs.py` (`Definitions`, found via `[tool.dagster]` in `pyproject.toml`). The ingestion asset key `ingest/weather_daily_files` matches the dbt source, which is what links it to `raw_weather_daily`.
- `data/out/` must exist for external models (dbt-duckdb does not create it) — hence the tracked `data/out/.gitkeep`.
- `data/report/` is kept the same way (`.gitkeep`, contents ignored).
- The notebook reads only `data/out/*.parquet` through an in-memory DuckDB, never `weather.duckdb`.

## Conventions

- Prod facts read only from staging models (`stg_weather_daily`, `stg_cities`), never from raw, seeds, or each other.
- Every model is written as CTEs: import CTEs, transform CTEs, then `final` and `select * from final`.
- Every model has an `id` = `dbt_utils.generate_surrogate_key` of its grain; facts carry `city_id` → `stg_cities.id`.
- One `schema.yml` per model folder (and `seeds/schema.yml`); no `_models.yml`-style files. The one exception is `models/raw/sources.yml`, which declares the data entering dbt. Cross-column checks go at model level (`dbt_utils.expression_is_true`), unit tests live in `models/prod/schema.yml`, custom SQL tests in `dbt/tests/`. A custom test that refs several models needs `config(meta={'dagster': {'ref': {'name': '<model>'}}})` to show up as an asset check in Dagster.
- Changing raw/seed columns requires `make transform ARGS="--full-refresh"`.
- Notebook charts must work in both light and dark marimo themes (marimo's `system` theme can't be detected from Python): transparent background, titles in `mo.md`, neutral grey chrome.
