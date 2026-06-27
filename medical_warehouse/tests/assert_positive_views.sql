-- Test: all view counts must be zero or positive
select *
from {{ ref('fct_messages') }}
where views < 0