"""Shared chart styling for the weather notebook."""

import altair as alt

# Fixed colour per city so a city keeps its colour across charts. Add one when a city is seeded.
CITY_COLORS = {
    "Göteborg": "#3987e5",
    "Örebro": "#d95926",
    "Stockholm": "#199e70",
    "Malmö": "#c98500",
    "Uppsala": "#d55181",
}
city_scale = alt.Scale(domain=list(CITY_COLORS), range=list(CITY_COLORS.values()))

# Mid-grey chrome that reads on both light and dark notebook themes.
MUTED = "#898781"


def style(chart):
    return (
        chart.configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            ticks=False,
            gridColor=MUTED,
            gridOpacity=0.25,
            labelColor=MUTED,
            titleColor=MUTED,
        )
        .configure_legend(labelColor=MUTED, title=None, symbolType="circle")
    )
