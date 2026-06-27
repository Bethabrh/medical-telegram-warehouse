-- Test: no messages should have a future date
select *
from {{ ref('fct_messages') }}
left join {{ ref('dim_dates') }} on fct_messages.date_key = dim_dates.date_key
where dim_dates.full_date > current_date