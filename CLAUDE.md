# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Make targets run from the repo root via `uv` (see `Makefile`); dbt itself runs from `dbt/`:

- `make transform [ARGS="--full-refresh" | ARGS="-s <model>"]` — `dbt build` (seeds, models, data tests, unit tests)
- `make viz` — `marimo run notebooks/weather.py`; use `uv run marimo edit ...` to edit
- `make orchestrate` — `dagster dev` (UI on :3000) with `DAGSTER_HOME=.dagster`; the only way to ingest. CLI: `uv run dagster asset materialize -m orchestrator.defs --select ingest/weather_daily_files --partition 2026-10` (or `--partition-range "2026-01...2026-09"`); each partition fetches every city
- Raw dbt: `cd dbt && uv run --env-file ../.env dbt <cmd>` (`profiles.yml` lives in `dbt/`)
- Unit tests only: `cd dbt && uv run dbt test --select test_type:unit`
- Lint: `uv run ruff check` / `uv run ruff format`; notebook: `uv run marimo check notebooks/weather.py`

## Architecture

Pipeline: Dagster asset `ingest/weather_daily_files` → `data/raw/<city>/<YYYY-MM>.parquet` → dbt (DuckDB file `$WEATHER_DB_PATH`, default `./weather.duckdb`) → `data/stg/<model>.parquet`, `data/prod/<model>.parquet` → marimo notebook.

- **Cities are defined once, in `dbt/seeds/cities.csv`.** `orchestrator/partitions.py` reads city keys and lat/lon from it. Adding a city also needs a colour in `CITY_COLORS` in the notebook.
- **Ingestion** (`OpenMeteoResource` in `orchestrator/resources.py`) validates each month with a pandera (polars) schema before writing; one file per city per month, overwritten on re-fetch. Uses the Open-Meteo *archive* API only (it covers up to today); no forecast API.
- **Adapter is `dbt-duckdb` (dbt-core 1.x), not dbt v2.** The `dbt` v2 package was removed because v2 has no `external` materialization; the two packages conflict over the `dbt` executable.
- **Layers / schemas:** `seeds` (seed `cities`), `staging` and `prod` (both `external` models: rebuilt in full each run and written to `data/stg` and `data/prod`; in the database they are views over those parquet files; `stg_weather_daily` reads the parquet files in `data/raw` directly). `external_root` is set per folder: `prod` uses the profile's (`profiles.yml`), `staging` overrides it in `dbt_project.yml`, which `macros/external_location.sql` (override of dbt-duckdb's macro) honours. `macros/generate_schema_name.sql` makes schema names literal (`staging`, not `main_staging`).
- **Data location comes from `WEATHER_DATA_DIR` in `.env`** (gitignored; template `.env.example`): the folder holding `raw/`, `stg/`, `prod/` and `report/`. dbt reads it via `env_var()` (`external_root` in `profiles.yml` and `dbt_project.yml`, the `raw/` glob in `models/staging/sources.yml`), Dagster and the notebook via `os.environ`; all fall back to `data/` in the repo when unset. `.env` is loaded by `dagster dev` (from the repo root) and by the Makefile (`UV_ENV_FILE`); raw `uv run` commands need `--env-file .env`. `WEATHER_DB_PATH` likewise sets the DuckDB file (`path` in `profiles.yml`). With both set dbt's paths are absolute; only the fallbacks (`../data`, `../weather.duckdb`) are relative to `dbt/`, because dagster-dbt always runs dbt with `dbt/` as working directory; the Makefile does the same. Other paths in `orchestrator/` are built from `__file__`.
- **Orchestration (Dagster)** lives in `orchestrator/`: `partitions.py` (monthly from 2024-01, keys `YYYY-MM`, each covering every city; also `CITIES` with coordinates), `resources.py` (`OpenMeteoResource`, the archive API client registered as resource `open_meteo`, plus the pandera schema), `assets.py` (ingestion asset returning polars frames via `OpenMeteoResource.fetch_month`, plus `@dbt_assets` running `dbt build`, plus `report/weather_html`: `marimo export html --no-include-code` of the notebook into `data/report/weather.html`, a snapshot with the year dropdown on its default), `io_managers.py` (splits each month partition by city into `data/raw/<city>/<YYYY-MM>.parquet`; assets hand it a dict of frames keyed by partition key, since the ingestion asset has a single-run backfill policy), `jobs.py` (`weather_monthly` job plus a schedule, off by default, that fetches last month for all cities in one run and builds dbt once) and `defs.py` (`Definitions`, found via `[tool.dagster]` in `pyproject.toml`). The ingestion asset key `ingest/weather_daily_files` matches the dbt source, which is what links it to `stg_weather_daily`.
- `data/stg/` and `data/prod/` must exist for external models (dbt-duckdb does not create them) — hence the tracked `.gitkeep` files (also in `data/raw/`).
- `data/report/` is kept the same way (`.gitkeep`, contents ignored).
- The notebook reads only `data/prod/*.parquet` through an in-memory DuckDB, never `weather.duckdb`.

## Conventions

- Prod facts read only from staging models (`stg_weather_daily`, `stg_cities`), never from sources, seeds, or each other.
- Every model is written as CTEs: import CTEs, transform CTEs, then `final` and `select * from final`.
- Every model has an `id` = `dbt_utils.generate_surrogate_key` of its grain; facts carry `city_id` → `stg_cities.id`.
- One `schema.yml` per model folder (and `seeds/schema.yml`); no `_models.yml`-style files. The one exception is `models/staging/sources.yml`, which declares the data entering dbt. Cross-column checks go at model level (`dbt_utils.expression_is_true`), unit tests live in `models/prod/schema.yml`, custom SQL tests in `dbt/tests/`. A custom test that refs several models needs `config(meta={'dagster': {'ref': {'name': '<model>'}}})` to show up as an asset check in Dagster.
- Changing seed columns requires `make transform ARGS="--full-refresh"`.
- Notebook charts must work in both light and dark marimo themes (marimo's `system` theme can't be detected from Python): transparent background, titles in `mo.md`, neutral grey chrome.
