"""Dagster definitions, loaded by `make orchestrate` (see [tool.dagster] in pyproject.toml)."""

import dagster as dg
from dagster_dbt import DbtCliResource

from orchestrator.assets import DATA_DIR, dbt_project, weather_daily_files, weather_dbt, weather_report
from orchestrator.io_managers import CityMonthParquetIOManager
from orchestrator.jobs import weather_monthly, weather_monthly_schedule
from orchestrator.resources import OpenMeteoResource

defs = dg.Definitions(
    assets=[weather_daily_files, weather_dbt, weather_report],
    jobs=[weather_monthly],
    schedules=[weather_monthly_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=dbt_project),
        "open_meteo": OpenMeteoResource(),
        "city_month_io_manager": CityMonthParquetIOManager(base_dir=str(DATA_DIR / "raw")),
    },
)
