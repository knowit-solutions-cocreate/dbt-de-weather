{{
    config(
        materialized='incremental',
        unique_key='id',
        incremental_strategy='delete+insert',
    )
}}

with source as (
    select * from {{ source('ingest', 'weather_daily_files') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['city', 'date']) }} as id,
        city,
        date,
        temperature_2m_max,
        temperature_2m_min,
        temperature_2m_mean,
        precipitation_sum,
        rain_sum,
        snowfall_sum,
        wind_speed_10m_max,
        sunshine_duration,
        ingested_at,
        filename as source_file
    from source
    {% if is_incremental() %}
        where ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
)

select * from final
