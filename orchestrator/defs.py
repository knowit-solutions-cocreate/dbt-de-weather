"""Dagster definitions, loaded by `make orchestrate` (see [tool.dagster] in pyproject.toml)."""

from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource

from orchestrator.assets import dbt_project, weather_daily_files, weather_dbt, weather_report
from orchestrator.io_managers import CityMonthParquetIOManager
from orchestrator.jobs import weather_monthly, weather_monthly_schedule
from orchestrator.resources import OpenMeteoResource

REPO_ROOT = Path(__file__).parent.parent

defs = dg.Definitions(
    assets=[weather_daily_files, weather_dbt, weather_report],
    jobs=[weather_monthly],
    schedules=[weather_monthly_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=dbt_project),
        "open_meteo": OpenMeteoResource(),
        "city_month_io_manager": CityMonthParquetIOManager(base_dir=str(REPO_ROOT / "data" / "in")),
    },
)
