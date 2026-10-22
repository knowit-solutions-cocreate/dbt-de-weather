-- The monthly rows of a city and year must add up to that city's yearly row.
-- Returns the (city, year) pairs that disagree; any row fails the test.
-- The test reads two models; meta.dagster.ref makes it an asset check on fct_weather_monthly.
{{ config(meta={'dagster': {'ref': {'name': 'fct_weather_monthly'}}}) }}

with monthly as (
    select
        city_id,
        year,
        sum(days_observed) as days_observed,
        sum(precipitation_mm) as precipitation_mm,
        sum(sunshine_hours) as sunshine_hours
    from {{ ref('fct_weather_monthly') }}
    group by city_id, year
),

yearly as (
    select city_id, year, days_observed, precipitation_mm, sunshine_hours
    from {{ ref('fct_weather_yearly') }}
),

final as (
    select
        coalesce(monthly.city_id, yearly.city_id) as city_id,
        coalesce(monthly.year, yearly.year) as year,
        monthly.days_observed as monthly_days,
        yearly.days_observed as yearly_days,
        monthly.precipitation_mm as monthly_precipitation_mm,
        yearly.precipitation_mm as yearly_precipitation_mm,
        monthly.sunshine_hours as monthly_sunshine_hours,
        yearly.sunshine_hours as yearly_sunshine_hours
    from monthly
    full outer join yearly
        on monthly.city_id = yearly.city_id
        and monthly.year = yearly.year
    where monthly.city_id is null
        or yearly.city_id is null
        or monthly.days_observed <> yearly.days_observed
        -- float sums in a different order can differ in the last digits
        or abs(monthly.precipitation_mm - yearly.precipitation_mm) > 0.001
        or abs(monthly.sunshine_hours - yearly.sunshine_hours) > 0.001
)

select * from final
