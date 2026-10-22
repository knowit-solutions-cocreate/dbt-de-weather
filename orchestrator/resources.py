"""Dagster resource for the Open-Meteo archive API (no API key), and the pandera schema its daily
weather is validated against."""

import calendar
import json
from datetime import UTC, date, datetime
from typing import Annotated
from urllib.parse import urlencode
from urllib.request import urlopen

import dagster as dg
import pandera.polars as pa
import polars as pl
from pandera.api.polars.model_config import BaseConfig

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


class DailyWeather(pa.DataFrameModel):
    city: str
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


class OpenMeteoResource(dg.ConfigurableResource):
    """Daily weather from the Open-Meteo archive, which covers up to today. The fields can be
    changed per run in the Dagster UI."""

    archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    timezone: str = "Europe/Stockholm"
    timeout_seconds: int = 30

    def fetch_daily(self, lat: float, lon: float, start: date, end: date) -> pl.DataFrame:
        params = urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": ",".join(DAILY_VARS),
                "timezone": self.timezone,
            }
        )
        with urlopen(f"{self.archive_url}?{params}", timeout=self.timeout_seconds) as resp:
            daily = json.load(resp)["daily"]
        return pl.DataFrame(daily).select(
            pl.col("time").str.to_date().alias("date"),
            pl.col(DAILY_VARS).cast(pl.Float64),
        )

    def fetch_month(self, city: str, lat: float, lon: float, year: int, month: int) -> pl.DataFrame:
        """One city's validated daily weather for one month, up to today."""
        start = date(year, month, 1)
        end = min(date(year, month, calendar.monthrange(year, month)[1]), date.today())
        df = self.fetch_daily(lat, lon, start, end).select(
            pl.lit(city).alias("city"),
            pl.all(),
            pl.lit(datetime.now(UTC)).alias("ingested_at"),
        )
        return DailyWeather.validate(df)
