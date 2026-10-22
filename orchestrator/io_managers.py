"""I/O manager that stores each city × month partition where dbt reads it."""

from pathlib import Path

import dagster as dg
import polars as pl

from orchestrator.partitions import city_month


class CityMonthParquetIOManager(dg.ConfigurableIOManager):
    """Writes city × month partitions to <base_dir>/<city>/<YYYY-MM>.parquet, the layout of the
    dbt source ingest.weather_daily_files. A run can cover several partitions, so assets hand over
    a dict of frames keyed by partition key."""

    base_dir: str

    def _path(self, partition_key: str) -> Path:
        keys = city_month.get_partition_key_from_str(partition_key).keys_by_dimension
        return Path(self.base_dir) / keys["city"] / f"{keys['month']}.parquet"

    def handle_output(self, context: dg.OutputContext, obj: dict[str, pl.DataFrame]) -> None:
        for partition_key, df in obj.items():
            path = self._path(partition_key)
            path.parent.mkdir(parents=True, exist_ok=True)
            df.write_parquet(path)
            context.log.info(f"{path}: {df.height} days")
        context.add_output_metadata(
            {"partitions": len(obj), "rows": sum(df.height for df in obj.values())}
        )

    def load_input(self, context: dg.InputContext) -> dict[str, pl.DataFrame]:
        return {key: pl.read_parquet(self._path(key)) for key in context.asset_partition_keys}
