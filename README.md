# dbt-de-weather

Daily weather for five Swedish cities (Göteborg, Örebro, Stockholm, Malmö, Uppsala), aggregated to
monthly and yearly figures.

## Overview

![Pipeline overview](docs/images/overview.png)

**Why save the API data as files?**

dbt can be re-run without calling the API again. There's one file per city and month, so fetching
a month again just overwrites that file, and the DuckDB database can always be rebuilt from `data/raw`.

**Why are the staging models written as files?**

Each layer is a folder of parquet files (`data/raw` -> `data/stg` -> `data/prod`), so every step's
output can be opened and inspected directly, without going through the DuckDB database.

**How is SQL executed?**

Two tools are used:

- **dbt**: turns SQL files into tables and views, in the right order
  - models: one `select` per file, in `staging/` and `prod/`
  - tests: checks on the data (unique ids, not null, monthly vs yearly totals)
- **DuckDB**: an analytical database that runs in-process (no server)

Since DuckDB reads and writes parquet natively, staging can query `data/raw` directly and the prod
models can be written straight to `data/prod` as parquet.

## Tools

| Step | Tool | What it does |
|---|---|---|
| Ingest | Python, polars, pandera | Fetches daily weather from the free [Open-Meteo archive API](https://open-meteo.com/) (no API key), validates it, and writes one parquet file per city per month |
| Transform | dbt + DuckDB (`dbt-duckdb`) | Loads the parquet files into a local DuckDB database, joins them with city data from a seed, and builds monthly and yearly tables that are exported to parquet |
| Viz | marimo, Altair | Notebook with a sunshine-per-city donut chart and a monthly rain line chart, read from the exported parquet files |

## Run it locally

Prerequisites: [uv](https://docs.astral.sh/uv/) and `make`. uv installs the right Python (3.12) and
all dependencies on first use.

```bash
git clone <repo-url> && cd dbt-de-weather

make ingest      # 1. fetch this year's weather up to today  -> data/raw/
make transform   # 2. build and test the dbt models          -> weather.duckdb, data/prod/
make viz         # 3. open the notebook as an app             -> http://localhost:2718
make docs        # optional: browse the dbt docs and lineage  -> http://localhost:8080
```

`make transform` installs the dbt packages (`dbt_utils`) the first time it runs.

### Options

```bash
make ingest YEAR=2025                    # a whole year
make ingest YEAR=2026 MONTH=10           # one month
make ingest YEAR=2026 MONTH=10 CITY=malmo

make transform ARGS="--full-refresh"     # rebuild everything, e.g. after changing the seed's columns
make transform ARGS="-s fct_weather_monthly"
```

Re-running `make ingest` for a month overwrites its files; the next `make transform` reads them
directly. To edit the notebook instead of viewing it: `uv run marimo edit notebooks/weather.py`.

## Repository structure

```
├── ingest_weather.py            # ingestion: Open-Meteo -> data/raw/<city>/<YYYY-MM>.parquet
├── dbt/                         # dbt project (run from the repo root, see Makefile)
│   ├── seeds/cities.csv         # cities with coordinates and attributes; also read by ingestion
│   ├── models/
│   │   ├── staging/             # stg_weather_daily (reads data/raw), stg_cities: renaming, unit conversion, ids
│   │   └── prod/                # fct_weather_monthly, fct_weather_yearly -> data/prod/*.parquet
│   ├── tests/                   # custom data tests (monthly vs yearly reconciliation)
│   ├── macros/                  # schema naming (seeds / staging / prod)
│   ├── profiles.yml             # DuckDB connection: ./weather.duckdb
│   └── packages.yml             # dbt_utils
├── notebooks/weather.py         # marimo notebook
├── data/
│   ├── raw/                     # ingested parquet (not committed)
│   ├── stg/                     # staging tables as parquet (not committed)
│   └── prod/                    # exported prod tables (not committed)
├── Makefile                     # ingest / transform / viz
└── pyproject.toml               # dependencies, ruff config
```

## Data model

Every table has an `id` (surrogate key of its grain) and is covered by dbt tests; `make transform`
also runs unit tests on the prod models before building them.

| Schema | Model | Grain |
|---|---|---|
| seeds | `cities` | city |
| staging | `stg_cities`, `stg_weather_daily` | city / city × day |
| prod | `fct_weather_monthly` | city × month |
| prod | `fct_weather_yearly` | city × year |

To add a city, add a row (with latitude and longitude) to `dbt/seeds/cities.csv`, run `make ingest`
and `make transform ARGS="--full-refresh"`, and give it a colour in `CITY_COLORS` in the notebook.
