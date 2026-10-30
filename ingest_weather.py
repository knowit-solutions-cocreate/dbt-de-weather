"""Fetch daily weather from the Open-Meteo archive for Swedish cities and write one parquet file
per city per month.
Cities and their coordinates come from the dbt seed (dbt/seeds/cities.csv).

Usage:
    uv run ingest_weather.py 2025                   # all cities, every month of 2025
    uv run ingest_weather.py 2026                   # all cities, January up to the current month
    uv run ingest_weather.py 2025 1                 # all cities, January 2025
    uv run ingest_weather.py 2026 10 --city orebro  # current month, up to today
"""

import argparse
import calendar
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode
from urllib.request import urlopen

import pandera.polars as pa
import polars as pl
from pandera.api.polars.model_config import BaseConfig

CITIES_SEED = Path("dbt/seeds/cities.csv")
CITIES = {
    row["city"]: (row["latitude"], row["longitude"])
    for row in pl.read_csv(CITIES_SEED).iter_rows(named=True)
}

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
    "sunshine_duration",
]

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OUT_DIR = Path("data/raw")


class DailyWeather(pa.DataFrameModel):
    city: str = pa.Field(isin=list(CITIES))
    date: pl.Date
    temperature_2m_max: float = pa.Field(nullable=True)
    temperature_2m_min: float = pa.Field(nullable=True)
    temperature_2m_mean: float = pa.Field(nullable=True)
    precipitation_sum: float = pa.Field(nullable=True, ge=0)  # mm
    rain_sum: float = pa.Field(nullable=True, ge=0)  # mm
    snowfall_sum: float = pa.Field(nullable=True, ge=0)  # cm
    wind_speed_10m_max: float = pa.Field(nullable=True, ge=0)  # km/h
    sunshine_duration: float = pa.Field(nullable=True)  # seconds
    ingested_at: Annotated[pl.Datetime, "us", "UTC"]

    class Config(BaseConfig):
        strict = True  # no unexpected columns
        unique = ["city", "date"]


def month_range(year: int, month: int) -> tuple[date, date]:
    today = date.today()
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return start, min(end, today)


def fetch_daily(lat: float, lon: float, start: date, end: date) -> pl.DataFrame:
    params = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": ",".join(DAILY_VARS),
            "timezone": "Europe/Stockholm",
        }
    )
    with urlopen(f"{ARCHIVE_URL}?{params}", timeout=30) as resp:
        daily = json.load(resp)["daily"]
    return pl.DataFrame(daily).select(
        pl.col("time").str.to_date().alias("date"),
        pl.col(DAILY_VARS).cast(pl.Float64),
    )


def write_month(city: str, year: int, month: int) -> None:
    lat, lon = CITIES[city]
    start, end = month_range(year, month)
    df = fetch_daily(lat, lon, start, end).select(
        pl.lit(city).alias("city"),
        pl.all(),
        pl.lit(datetime.now(UTC)).alias("ingested_at"),
    )
    df = DailyWeather.validate(df)
    path = OUT_DIR / city / f"{year}-{month:02d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    print(f"{path}: {df.height} days ({start} -> {end})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("year", type=int)
    parser.add_argument(
        "month",
        type=int,
        nargs="?",
        choices=range(1, 13),
        metavar="month",
        help="default: every month of the year, up to the current month",
    )
    parser.add_argument("--city", choices=CITIES, help="default: all cities")
    args = parser.parse_args()

    months = [args.month] if args.month else range(1, 13)
    months = [m for m in months if date(args.year, m, 1) <= date.today()]
    if not months:
        parser.error("requested month(s) are in the future")

    for city in [args.city] if args.city else CITIES:
        for month in months:
            write_month(city, args.year, month)


if __name__ == "__main__":
    main()
