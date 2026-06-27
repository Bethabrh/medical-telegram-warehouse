-- Dimension table: one row per Telegram channel

with channel_stats as (
    select
        channel_username,
        channel_name,
        min(message_date_day)       as first_post_date,
        max(message_date_day)       as last_post_date,
        count(*)                    as total_posts,
        avg(views)                  as avg_views,
        case
            when lower(channel_name) like '%pharma%'
              or lower(channel_name) like '%drug%'
              or lower(channel_name) like '%medicine%'
              or lower(channel_username) like '%pharma%'
            then 'Pharmaceutical'
            when lower(channel_name) like '%cosmet%'
              or lower(channel_name) like '%beauty%'
              or lower(channel_name) like '%lobelia%'
            then 'Cosmetics'
            else 'Medical'
        end                         as channel_type
    from {{ ref('stg_telegram_messages') }}
    group by channel_username, channel_name
)

select
    row_number() over (order by channel_username) as channel_key,
    channel_username,
    channel_name,
    channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    round(avg_views::numeric, 2)  as avg_views
from channel_stats