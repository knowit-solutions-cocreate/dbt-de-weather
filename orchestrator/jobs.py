"""Monthly job: fetch last month for every city, then build the dbt project."""

from datetime import timedelta

import dagster as dg

from orchestrator.partitions import monthly

weather_monthly = dg.define_asset_job(
    "weather_monthly",
    selection=dg.AssetSelection.groups("weather"),
    partitions_def=monthly,
)


@dg.schedule(
    job=weather_monthly,
    cron_schedule="0 6 2 * *",
    execution_timezone="Europe/Stockholm",
    default_status=dg.DefaultScheduleStatus.STOPPED,
)
def weather_monthly_schedule(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    last_month = context.scheduled_execution_time.replace(day=1) - timedelta(days=1)
    month = last_month.strftime("%Y-%m")
    return dg.RunRequest(run_key=month, partition_key=month)
