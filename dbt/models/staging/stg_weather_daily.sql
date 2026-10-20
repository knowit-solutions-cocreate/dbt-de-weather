with source as (
    select * from {{ ref('raw_weather_daily') }}
),

final as (
    select
        id,
        {{ dbt_utils.generate_surrogate_key(['city']) }} as city_id,
        city,
        date,
        date_trunc('month', date)::date as month_start,
        year(date) as year,
        temperature_2m_max as temp_max_c,
        temperature_2m_min as temp_min_c,
        temperature_2m_mean as temp_mean_c,
        precipitation_sum as precipitation_mm,
        rain_sum as rain_mm,
        snowfall_sum as snowfall_cm,
        wind_speed_10m_max as wind_max_kmh,
        sunshine_duration / 3600 as sunshine_hours,
        ingested_at
    from source
)

select * from final
