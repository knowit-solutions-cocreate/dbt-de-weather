import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    from pathlib import Path

    import altair as alt
    import duckdb
    import marimo as mo

    return Path, alt, duckdb, mo, os


@app.cell
def _(Path, duckdb, mo, os):
    # In-memory DuckDB over the dbt outputs in data/out; weather.duckdb is never opened.
    # WEATHER_DATA_DIR comes from .env (see .env.example), like in dbt and Dagster.
    out_dir = Path(os.environ.get("WEATHER_DATA_DIR", mo.notebook_dir().parent / "data")) / "out"
    con = duckdb.connect(":memory:")
    for _view in ["monthly", "yearly"]:
        _path = out_dir / f"fct_weather_{_view}.parquet"
        con.sql(f"create view {_view} as select * from read_parquet('{_path}')")
    return (con,)


@app.cell
def _(alt):
    # Fixed colour per city, so a city keeps its colour across charts and filters. These are the
    # dark-surface steps of the validated categorical palette: they pass on both light and dark
    # backgrounds, which matters because marimo's "system" theme can't be detected from Python.
    # Add a slot here when a city is added to the seed.
    CITY_COLORS = {
        "Göteborg": "#3987e5",
        "Örebro": "#d95926",
        "Stockholm": "#199e70",
        "Malmö": "#c98500",
        "Uppsala": "#d55181",
    }
    city_scale = alt.Scale(domain=list(CITY_COLORS), range=list(CITY_COLORS.values()))

    # Theme-neutral chrome: transparent background, mid-grey text, translucent hairline grid.
    # Titles live in marimo markdown, which follows the notebook theme.
    MUTED = "#898781"
    INK_ON_COLOR = "#0b0b0b"  # text drawn on top of a coloured mark

    def style(chart):
        return (
            chart.configure(background="transparent", font="system-ui, sans-serif")
            .configure_view(stroke=None)
            .configure_axis(
                domain=False,
                ticks=False,
                gridColor=MUTED,
                gridOpacity=0.25,
                labelColor=MUTED,
                titleColor=MUTED,
                labelFontSize=12,
                titleFontSize=12,
                titleFontWeight="normal",
                labelPadding=6,
            )
            .configure_legend(
                labelColor=MUTED,
                titleColor=MUTED,
                labelFontSize=12,
                title=None,
                symbolType="circle",
                symbolSize=120,
                orient="right",
            )
        )

    return INK_ON_COLOR, MUTED, city_scale, style


@app.cell
def _(mo):
    mo.md("""
    # Weather in Swedish cities

    Built from the dbt outputs `fct_weather_yearly.parquet` and `fct_weather_monthly.parquet`.
    """)
    return


@app.cell
def _(con, mo):
    _rows = con.sql("select distinct year from yearly order by year").fetchall()
    years = [str(y) for (y,) in _rows]
    year = mo.ui.dropdown(options=years, value=years[-1], label="Year")
    return (year,)


@app.cell
def _(con, year):
    sunshine = con.sql(
        """
        select
            city_name,
            round(sunshine_hours) as sunshine_hours,
            round(100 * sunshine_hours / sum(sunshine_hours) over (), 1) as share_pct,
            days_observed,
            is_complete_year
        from yearly
        where year = $year
        order by city_name
        """,
        params={"year": int(year.value)},
    ).pl()
    return (sunshine,)


@app.cell
def _(INK_ON_COLOR, alt, city_scale, mo, style, sunshine, year):
    _total = int(sunshine["sunshine_hours"].sum())
    _partial = (
        ""
        if sunshine["is_complete_year"].all()
        else f" · partial year, {sunshine['days_observed'].max()} days so far"
    )

    _base = alt.Chart(sunshine).encode(
        theta=alt.Theta("sunshine_hours:Q", stack=True),
        order=alt.Order("city_name:N"),
    )
    _ring = _base.mark_arc(innerRadius=90, outerRadius=160, padAngle=0.015, cornerRadius=4).encode(
        color=alt.Color("city_name:N", scale=city_scale),
        tooltip=[
            alt.Tooltip("city_name:N", title="City"),
            alt.Tooltip("sunshine_hours:Q", title="Sunshine (h)", format=",.0f"),
            alt.Tooltip("share_pct:Q", title="Share (%)", format=".1f"),
        ],
    )
    _labels = _base.mark_text(radius=125, fontSize=13, fontWeight=600, color=INK_ON_COLOR).encode(
        text=alt.Text("share_pct:Q", format=".1f")
    )

    sunshine_chart = style((_ring + _labels).properties(width=360, height=360))

    mo.vstack(
        [
            mo.hstack(
                [
                    mo.md(f"## Sunshine by city, {year.value}"),
                    year,
                ],
                justify="space-between",
                align="center",
            ),
            mo.md(f"Share of {_total:,} total sunshine hours, in %{_partial}"),
            mo.ui.tabs({"Chart": sunshine_chart, "Table": mo.ui.table(sunshine, selection=None)}),
        ]
    )
    return


@app.cell
def _(con, year):
    temp_range = con.sql(
        """
        select
            city_name,
            round(latitude, 1) as latitude,
            if(is_coastal, 'Coastal', 'Inland') as setting,
            round(min_temp_c, 1) as min_temp_c,
            round(avg_temp_c, 1) as avg_temp_c,
            round(max_temp_c, 1) as max_temp_c,
            round(max_temp_c - min_temp_c, 1) as range_c,
            days_observed,
            is_complete_year
        from yearly
        where year = $year
        order by latitude
        """,
        params={"year": int(year.value)},
    ).pl()
    return (temp_range,)


@app.cell
def _(MUTED, alt, city_scale, mo, style, temp_range, year):
    # Weather meets city attributes: rows run south to north (latitude), coastal cities get filled
    # end points and inland cities hollow ones.
    _partial = (
        ""
        if temp_range["is_complete_year"].all()
        else f" Partial year, {temp_range['days_observed'].max()} days so far."
    )

    _y = alt.Y(
        "city_name:N",
        title=None,
        sort=alt.EncodingSortField("latitude", order="ascending"),
        axis=alt.Axis(grid=False),
    )
    _x = alt.X("min_temp_c:Q", title="°C", axis=alt.Axis(tickCount=8))
    _color = alt.Color("city_name:N", scale=city_scale, legend=None)
    _tooltip = [
        alt.Tooltip("city_name:N", title="City"),
        alt.Tooltip("setting:N", title="Setting"),
        alt.Tooltip("latitude:Q", title="Latitude (°N)", format=".1f"),
        alt.Tooltip("min_temp_c:Q", title="Coldest day (°C)", format=".1f"),
        alt.Tooltip("avg_temp_c:Q", title="Average (°C)", format=".1f"),
        alt.Tooltip("max_temp_c:Q", title="Warmest day (°C)", format=".1f"),
        alt.Tooltip("range_c:Q", title="Range (°C)", format=".1f"),
    ]
    _base = alt.Chart(temp_range).encode(y=_y, tooltip=_tooltip)

    _freezing = (
        alt.Chart(alt.Data(values=[{"zero": 0}]))
        .mark_rule(color=MUTED, strokeWidth=1, strokeDash=[3, 3], opacity=0.6)
        .encode(x="zero:Q")
    )
    _bar = _base.mark_rule(strokeWidth=2, strokeCap="round").encode(
        x=_x, x2="max_temp_c:Q", color=_color
    )
    _avg = _base.mark_tick(color=MUTED, thickness=3, size=16).encode(x="avg_temp_c:Q")
    _fill = alt.condition(
        "datum.setting === 'Coastal'",
        alt.Color("city_name:N", scale=city_scale, legend=None),
        alt.value("transparent"),
    )
    _ends = [
        _base.mark_point(size=110, strokeWidth=2, opacity=1).encode(
            x=f"{_field}:Q", stroke=_color, fill=_fill
        )
        for _field in ["min_temp_c", "max_temp_c"]
    ]
    _labels = [
        _base.mark_text(align=_align, dx=_dx, fontSize=12, color=MUTED).encode(
            x=f"{_field}:Q", text=alt.Text(f"{_field}:Q", format=".1f")
        )
        for _field, _align, _dx in [("min_temp_c", "right", -10), ("max_temp_c", "left", 10)]
    ]

    temp_range_chart = style(
        alt.layer(_freezing, _bar, _avg, *_ends, *_labels).properties(width="container", height=240)
    )

    mo.vstack(
        [
            mo.md(f"## Temperature range by city, {year.value}"),
            mo.md(
                "Coldest to warmest day of the year; the grey tick is the average. Cities run "
                "south to north (latitude); filled ends are coastal cities, hollow ends inland "
                f"ones.{_partial}"
            ),
            mo.ui.tabs(
                {"Chart": temp_range_chart, "Table": mo.ui.table(temp_range, selection=None)}
            ),
        ]
    )
    return


@app.cell
def _(con):
    rain = con.sql(
        """
        select
            city_name,
            month_start,
            round(rain_mm / days_observed, 2) as avg_daily_rain_mm,
            round(rain_mm, 1) as rain_mm,
            days_observed,
            is_complete_month
        from monthly
        order by city_name, month_start
        """
    ).pl()
    return (rain,)


@app.cell
def _(MUTED, alt, city_scale, mo, rain, style):
    # Click a city in the legend to highlight it; hover anywhere to see that month's values.
    _city = alt.selection_point(fields=["city_name"], bind="legend")
    _hover = alt.selection_point(
        fields=["month_start"], nearest=True, on="pointerover", empty=False, clear="pointerout"
    )

    _x = alt.X(
        "month_start:T",
        title=None,
        axis=alt.Axis(format="%b %Y", tickCount={"interval": "month", "step": 3}, grid=False),
    )
    _y = alt.Y("avg_daily_rain_mm:Q", title="mm per day", axis=alt.Axis(tickCount=5))
    _color = alt.Color("city_name:N", scale=city_scale)
    _base = alt.Chart(rain).encode(x=_x)

    _lines = (
        _base.mark_line(strokeWidth=2, strokeCap="round", strokeJoin="round")
        .encode(
            y=_y,
            color=_color,
            opacity=alt.condition(_city, alt.value(1), alt.value(0.15)),
        )
        .add_params(_city)
    )
    _rule = (
        _base.mark_rule(color=MUTED, strokeWidth=1)
        .encode(opacity=alt.condition(_hover, alt.value(0.6), alt.value(0)))
        .add_params(_hover)
    )
    _points = _base.mark_point(filled=True, size=70).encode(
        y=_y,
        color=_color,
        opacity=alt.condition(_hover & _city, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("city_name:N", title="City"),
            alt.Tooltip("month_start:T", title="Month", format="%B %Y"),
            alt.Tooltip("avg_daily_rain_mm:Q", title="Avg daily rain (mm)", format=".2f"),
            alt.Tooltip("rain_mm:Q", title="Month total (mm)", format=".1f"),
            alt.Tooltip("days_observed:Q", title="Days observed"),
        ],
    )

    rain_chart = style((_lines + _rule + _points).properties(width="container", height=320))

    mo.vstack(
        [
            mo.md("## Average daily rain per month"),
            mo.md(
                "Monthly rain divided by days observed, so the current partial month compares "
                "fairly. Click a city in the legend to highlight it."
            ),
            mo.ui.tabs({"Chart": rain_chart, "Table": mo.ui.table(rain, selection=None)}),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
