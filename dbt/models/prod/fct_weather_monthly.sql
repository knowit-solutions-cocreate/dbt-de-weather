with weather_daily as (
    select * from {{ ref('stg_weather_daily') }}
),

cities as (
    select * from {{ ref('stg_cities') }}
),

monthly as (
    select
        city_id,
        city,
        month_start,
        any_value(year) as year,
        count(*) as days_observed,
        day(last_day(month_start)) as days_in_month,
        avg(temp_mean_c) as avg_temp_c,
        max(temp_max_c) as max_temp_c,
        min(temp_min_c) as min_temp_c,
        sum(precipitation_mm) as precipitation_mm,
        sum(rain_mm) as rain_mm,
        sum(snowfall_cm) as snowfall_cm,
        count_if(precipitation_mm >= 1) as wet_days,
        max(wind_max_kmh) as max_wind_kmh,
        sum(sunshine_hours) as sunshine_hours
    from weather_daily
    group by city_id, city, month_start
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['monthly.city', 'monthly.month_start']) }} as id,
        monthly.city_id,
        monthly.city,
        cities.city_name,
        cities.county,
        cities.region,
        cities.population,
        cities.elevation_m,
        cities.is_coastal,
        monthly.year,
        monthly.month_start,
        monthly.days_observed,
        monthly.days_in_month,
        monthly.days_observed = monthly.days_in_month as is_complete_month,
        monthly.avg_temp_c,
        monthly.max_temp_c,
        monthly.min_temp_c,
        monthly.precipitation_mm,
        monthly.rain_mm,
        monthly.snowfall_cm,
        monthly.wet_days,
        monthly.max_wind_kmh,
        monthly.sunshine_hours
    from monthly
    inner join cities on monthly.city_id = cities.id
)

select * from final
