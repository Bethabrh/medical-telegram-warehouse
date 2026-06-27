-- Fact table: one row per message

with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channels as (
    select * from {{ ref('dim_channels') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
)

select
    m.message_id,
    c.channel_key,
    d.date_key,
    m.message_text,
    m.message_length,
    m.views,
    m.forwards,
    m.has_media,
    m.has_image,
    m.image_path
from messages m
left join channels c
    on m.channel_username = c.channel_username
left join dates d
    on m.message_date_day = d.full_date