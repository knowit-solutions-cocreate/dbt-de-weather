"""I/O manager that stores each month partition where dbt reads it, one file per city."""

from pathlib import Path

import dagster as dg
import polars as pl


class CityMonthParquetIOManager(dg.ConfigurableIOManager):
    """Writes month partitions to <base_dir>/<city>/<YYYY-MM>.parquet, the layout of the dbt
    source ingest.weather_daily_files. A run can cover several partitions, so assets hand over a
    dict of frames (all cities) keyed by partition key."""

    base_dir: str

    def handle_output(self, context: dg.OutputContext, obj: dict[str, pl.DataFrame]) -> None:
        for month, df in obj.items():
            for (city,), city_df in df.partition_by("city", as_dict=True).items():
                path = Path(self.base_dir) / city / f"{month}.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                city_df.write_parquet(path)
                context.log.info(f"{path}: {city_df.height} days")
        context.add_output_metadata(
            {"partitions": len(obj), "rows": sum(df.height for df in obj.values())}
        )

    def load_input(self, context: dg.InputContext) -> dict[str, pl.DataFrame]:
        return {
            month: pl.read_parquet(Path(self.base_dir) / "*" / f"{month}.parquet")
            for month in context.asset_partition_keys
        }
