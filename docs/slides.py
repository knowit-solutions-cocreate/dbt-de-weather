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
    mo.vstack(
        [
            mo.image(mo.notebook_dir() / "images" / "overview.png", height="30vh"),
            mo.md("""
            1. **Ingestion** of data from external sources
            2. **Transformation** of data and **join** with internal data
            3. **Outcome** visualization
            """),
        ],
        align="center",
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
                    - Pre-defined paths based on use-case (i.e. cities)
                    - bash script for execution
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
                    - Data tests per column and across tables, unit tests for the logic
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
                    mo.md("## Analysis/Visualization"),
                    mo.md("""
                    Using a Python based notebook to analyze and visualize the data.
                    """),
                ]
            ),
            mo.image(mo.notebook_dir() / "images" / "analysis.png", width="100%"),
        ],
        align="center",
        widths=[3, 2],
    )
    return


if __name__ == "__main__":
    app.run()
