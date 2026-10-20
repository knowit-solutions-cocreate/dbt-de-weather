with source as (
    select * from {{ ref('cities') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['city']) }} as id,
        city,
        city_name,
        county,
        region,
        latitude,
        longitude,
        population,
        elevation_m,
        is_coastal,
        founded_year
    from source
)

select * from final
