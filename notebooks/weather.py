import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import polars as pl
    from theme import city_scale, style

    return alt, city_scale, mo, pl, style


@app.cell
def _(mo, pl):
    monthly = pl.read_parquet(
        mo.notebook_dir().parent / "data" / "out" / "fct_weather_monthly.parquet"
    )
    return (monthly,)


@app.cell
def _(mo, monthly, pl):
    _months = monthly.select("month_start", "is_complete_month", "days_observed", "days_in_month")
    _first, _last = _months["month_start"].min(), _months["month_start"].max()
    _n = _months["month_start"].n_unique()
    _partial = _months.filter(~pl.col("is_complete_month")).unique("month_start")
    _partial_note = "".join(
        f" · {r['month_start']:%b %Y} is partial "
        f"({r['days_observed']} of {r['days_in_month']} days)"
        for r in _partial.iter_rows(named=True)
    )

    mo.md(f"""
    # Weather in Swedish cities

    Covering **{_first:%b %Y} – {_last:%b %Y}** ({_n} months){_partial_note}.
    Built from the dbt output `fct_weather_monthly.parquet`.
    """)
    return


@app.cell
def _(monthly, pl):
    sunshine = (
        monthly.group_by("city_name")
        .agg(pl.col("sunshine_hours").sum())
        .with_columns(
            pl.col("sunshine_hours").round(),
            (100 * pl.col("sunshine_hours") / pl.col("sunshine_hours").sum())
            .round(1)
            .alias("share_pct"),
        )
        .sort("city_name")
    )
    return (sunshine,)


@app.cell
def _(alt, city_scale, mo, style, sunshine):
    _base = alt.Chart(sunshine).encode(
        theta=alt.Theta("sunshine_hours:Q", stack=True),
        order=alt.Order("city_name:N"),
    )
    _ring = _base.mark_arc(innerRadius=90, outerRadius=160).encode(
        color=alt.Color("city_name:N", scale=city_scale),
        tooltip=["city_name:N", "sunshine_hours:Q", "share_pct:Q"],
    )
    _labels = _base.mark_text(radius=125, fontWeight=600).encode(
        text=alt.Text("share_pct:Q", format=".1f")
    )
    sunshine_chart = style((_ring + _labels).properties(width=360, height=360))

    mo.vstack(
        [
            mo.md("## ☀️ Sunshine by city"),
            mo.md(f"Share of {int(sunshine['sunshine_hours'].sum()):,} total sunshine hours, in %"),
            mo.ui.tabs({"Chart": sunshine_chart, "Table": mo.ui.table(sunshine, selection=None)}),
        ]
    )
    return


@app.cell
def _(monthly, pl):
    precip = monthly.select(
        "city_name",
        "month_start",
        (pl.col("precipitation_mm") / pl.col("days_observed")).round(2).alias("avg_daily_mm"),
        pl.col("precipitation_mm").round(1),
        "days_observed",
    ).sort("city_name", "month_start")
    return (precip,)


@app.cell
def _(alt, city_scale, mo, precip, style):
    _chart = (
        alt.Chart(precip)
        .mark_line(point=True)
        .encode(
            x=alt.X("month_start:T", title=None, axis=alt.Axis(format="%b %Y", grid=False)),
            y=alt.Y("avg_daily_mm:Q", title="mm per day"),
            color=alt.Color("city_name:N", scale=city_scale),
            tooltip=[
                "city_name:N",
                alt.Tooltip("month_start:T", format="%B %Y"),
                "avg_daily_mm:Q",
                "precipitation_mm:Q",
                "days_observed:Q",
            ],
        )
    )
    precip_chart = style(_chart.properties(width="container", height=320))

    mo.vstack(
        [
            mo.md("## 🌧️ Average daily precipitation per month"),
            mo.md(
                "Rain and snow (as water), divided by days observed so a partial month "
                "compares fairly."
            ),
            mo.ui.tabs({"Chart": precip_chart, "Table": mo.ui.table(precip, selection=None)}),
        ]
    )
    return


@app.cell
def _(monthly, pl):
    snow = (
        monthly.group_by("city_name", "year")
        .agg(pl.col("snowfall_cm").sum().round(1), pl.col("days_observed").sum())
        .sort("city_name", "year")
    )
    return (snow,)


@app.cell
def _(alt, mo, snow, style):
    _chart = (
        alt.Chart(snow)
        .mark_bar()
        .encode(
            x=alt.X("city_name:N", title=None, axis=alt.Axis(labelAngle=0)),
            xOffset="year:O",
            y=alt.Y("snowfall_cm:Q", title="cm"),
            color=alt.Color("year:O"),
            tooltip=["city_name:N", "year:O", "snowfall_cm:Q", "days_observed:Q"],
        )
        .properties(width="container", height=280)
    )
    snow_chart = style(_chart)

    mo.vstack(
        [
            mo.md("## ❄️ Annual snowfall per city"),
            mo.md("Total snowfall per year. The latest year is partial, see the coverage above."),
            mo.ui.tabs({"Chart": snow_chart, "Table": mo.ui.table(snow, selection=None)}),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
