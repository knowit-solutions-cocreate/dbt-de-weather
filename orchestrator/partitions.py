"""Ingestion partitions: one per city per month, like data/in/<city>/<YYYY-MM>.parquet."""

from pathlib import Path

import dagster as dg
import polars as pl

# Cities and their coordinates come from the dbt seed
CITIES_SEED = Path(__file__).parent.parent / "dbt" / "seeds" / "cities.csv"
CITIES = {
    row["city"]: (row["latitude"], row["longitude"])
    for row in pl.read_csv(CITIES_SEED).iter_rows(named=True)
}

city_month = dg.MultiPartitionsDefinition(
    {
        "city": dg.StaticPartitionsDefinition(list(CITIES)),
        # Keys like 2024-01, the file name in data/in; end_offset=1 adds the current month
        "month": dg.MonthlyPartitionsDefinition(start_date="2024-01", fmt="%Y-%m", end_offset=1),
    }
)
