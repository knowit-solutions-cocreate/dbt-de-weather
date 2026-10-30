import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="medium",
    layout_file="layouts/slides.slides.json",
    css_file="slides.css",
)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.vstack(
        [
            mo.md("# A sample data engineering project"),
            mo.image(mo.notebook_dir() / "images" / "overview.png", width="100%"),
        ]
    )
    return


@app.cell
def _(mo):
    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("## Ingestion"),
                    mo.md("""
                    Using Python script to collect data from external sources (Weather API).

                    Data can be stored on specific directories as parquet files,
                    partitioned by month.
                    - Collect only the partition interested in - Do not stress the API
                    - store data files under specific paths
                    - execution by running the parameterized python script
                    """),
                ]
            ),
            mo.image(mo.notebook_dir() / "images" / "ingestion.png", width="100%"),
        ],
        align="center",
        widths=[3, 2],
    )
    return


@app.cell
def _(mo):
    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("## Transformation"),
                    mo.md("""
                    Using dbt with DuckDB to clean, test and combine the raw files
                    with internal data (i.e. cities metadata).
                    The SQL runs in-process with DuckDB - no database server.

                    Staging models are views over the raw parquet files,
                    prod models are written back as parquet files.
                    - Staging - collect and normalize
                    - Production - aggregations and transformations
                    - Data tests per column and across tables
                    - Metadata (descriptions, tests) versioned in git next to the SQL
                    """),
                ]
            ),
            mo.image(mo.notebook_dir() / "images" / "transformation.png", width="100%"),
        ],
        align="center",
        widths=[3, 2],
    )
    return


@app.cell
def _(mo):
    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("## Serve"),
                    mo.md("""
                    Using a Python based notebook to analyze and visualize the produced data.
                    """),
                ]
            ),
            mo.image(mo.notebook_dir() / "images" / "analysis.png", width="100%"),
        ],
        align="center",
        widths=[3, 2],
    )
    return


@app.cell
def _(mo):
    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("## Moving to Production"),
                    mo.md("""
                    Production requirements are defined based on the stakeholder needs (i.e. refresh rate).
                    An orchestrator like Dagster can be used to materialize the project
                    on a fixed schedule (i.e. daily/monthly).

                    - **Ingestion**: modify python script to dagster asset logic with monthly partitions.
                    - **Transformation**: Load dbt project into dagster
                    - **Visualization**: Export static html to a new dir.
                    """),
                ]
            ),
            mo.image(mo.notebook_dir() / "images" / "dagster.png", width="100%"),
        ],
        align="center",
        widths=[1, 1],
    )
    return


if __name__ == "__main__":
    app.run()
