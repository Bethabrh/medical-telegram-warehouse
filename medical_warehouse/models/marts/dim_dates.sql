-- Dimension table: one row per date found in messages

with dates as (
    select distinct message_date_day as full_date
    from {{ ref('stg_telegram_messages') }}
    where message_date_day is not null
)

select
    to_char(full_date, 'YYYYMMDD')::integer   as date_key,
    full_date,
    extract(dow from full_date)::integer       as day_of_week,
    to_char(full_date, 'Day')                  as day_name,
    extract(week from full_date)::integer      as week_of_year,
    extract(month from full_date)::integer     as month,
    to_char(full_date, 'Month')                as month_name,
    extract(quarter from full_date)::integer   as quarter,
    extract(year from full_date)::integer      as year,
    case
        when extract(dow from full_date) in (0, 6) then true
        else false
    end                                        as is_weekend
from dates