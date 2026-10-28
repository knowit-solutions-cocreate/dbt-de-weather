"""Dagster assets: the Open-Meteo ingestion, partitioned by month, the dbt project, and
the notebook exported as an HTML report."""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import dagster as dg
import polars as pl
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets, get_asset_key_for_model

from orchestrator.partitions import CITIES, monthly
from orchestrator.resources import OpenMeteoResource

REPO_ROOT = Path(__file__).parent.parent
NOTEBOOK = REPO_ROOT / "notebooks" / "weather.py"
# Holds in/, out/ and report/; set in .env (see .env.example), defaults to data/ in the repo.
DATA_DIR = Path(os.environ.get("WEATHER_DATA_DIR", REPO_ROOT / "data"))
REPORT = DATA_DIR / "report" / "weather.html"

dbt_project = DbtProject(project_dir=REPO_ROOT / "dbt")
dbt_project.prepare_if_dev()  # parses the dbt project into target/manifest.json under `dagster dev`


@dg.asset(
    key=["ingest", "weather_daily_files"],
    partitions_def=monthly,
    io_manager_key="city_month_io_manager",
    group_name="weather",
    kinds={"python"},
    backfill_policy=dg.BackfillPolicy.single_run(),
    description="Daily weather for every city, per month, fetched from the Open-Meteo archive.",
)
def weather_daily_files(
    context: dg.AssetExecutionContext, open_meteo: OpenMeteoResource
) -> dict[str, pl.DataFrame]:
    frames = {}
    for partition_key in context.partition_keys:
        month = datetime.strptime(partition_key, "%Y-%m")
        frames[partition_key] = pl.concat(
            open_meteo.fetch_month(city, lat, lon, month.year, month.month)
            for city, (lat, lon) in CITIES.items()
        )
    return frames


@dbt_assets(manifest=dbt_project.manifest_path)
def weather_dbt(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@dg.asset(
    key=["report", "weather_html"],
    deps=[
        get_asset_key_for_model([weather_dbt], "fct_weather_monthly"),
        get_asset_key_for_model([weather_dbt], "fct_weather_yearly"),
    ],
    group_name="weather",
    kinds={"marimo"},
    description=(
        "The marimo notebook as static HTML, without code. A snapshot: the year dropdown stays on "
        "its default, the latest year; `make viz` is the interactive version."
    ),
)
def weather_report() -> dg.MaterializeResult:
    subprocess.run(
        [sys.executable, "-m", "marimo", "export", "html", str(NOTEBOOK)]
        + ["--output", str(REPORT), "--no-include-code", "--force"],
        check=True,
    )
    return dg.MaterializeResult(metadata={"path": dg.MetadataValue.path(str(REPORT))})
