"""Monthly job: fetch last month for every city, then build the dbt project."""

from datetime import timedelta

import dagster as dg

from orchestrator.partitions import city_month

weather_monthly = dg.define_asset_job(
    "weather_monthly",
    selection=dg.AssetSelection.groups("weather"),
    partitions_def=city_month,
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
    cities = city_month.get_partitions_def_for_dimension("city").get_partition_keys()
    # A range over both dimensions: every city, one month, in a single run
    first = dg.MultiPartitionKey({"city": cities[0], "month": month})
    last = dg.MultiPartitionKey({"city": cities[-1], "month": month})
    return dg.RunRequest(
        run_key=month,
        tags={
            "dagster/asset_partition_range_start": first,
            "dagster/asset_partition_range_end": last,
        },
    )
