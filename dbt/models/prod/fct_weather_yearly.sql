with weather_daily as (
    select * from {{ ref('stg_weather_daily') }}
),

cities as (
    select * from {{ ref('stg_cities') }}
),

yearly as (
    select
        city_id,
        city,
        year,
        count(distinct month_start) as months_observed,
        count(*) as days_observed,
        dayofyear(make_date(year, 12, 31)) as days_in_year,
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
    group by city_id, city, year
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['yearly.city', 'yearly.year']) }} as id,
        yearly.city_id,
        yearly.city,
        cities.city_name,
        cities.county,
        cities.region,
        cities.latitude,
        cities.longitude,
        cities.population,
        cities.elevation_m,
        cities.is_coastal,
        yearly.year,
        yearly.months_observed,
        yearly.days_observed,
        yearly.days_in_year,
        yearly.days_observed = yearly.days_in_year as is_complete_year,
        yearly.avg_temp_c,
        yearly.max_temp_c,
        yearly.min_temp_c,
        yearly.precipitation_mm,
        yearly.rain_mm,
        yearly.snowfall_cm,
        yearly.wet_days,
        yearly.max_wind_kmh,
        yearly.sunshine_hours
    from yearly
    inner join cities on yearly.city_id = cities.id
)

select * from final
