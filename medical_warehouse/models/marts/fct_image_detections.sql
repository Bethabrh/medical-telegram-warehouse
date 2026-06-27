-- Fact table: YOLO object detection results per image

with yolo as (
    select * from raw.yolo_detections
),

messages as (
    select * from {{ ref('fct_messages') }}
),

channels as (
    select * from {{ ref('dim_channels') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
)

select
    y.message_id::integer                    as message_id,
    c.channel_key                            as channel_key,
    d.date_key                               as date_key,
    y.channel_name                           as channel_name,
    y.detected_class                         as detected_class,
    y.confidence_score                       as confidence_score,
    y.all_detected_classes                   as all_detected_classes,
    y.image_category                         as image_category,
    y.total_detections                       as total_detections,
    m.views                                  as message_views,
    m.forwards                               as message_forwards
from yolo y
left join messages m
    on y.message_id::integer = m.message_id
left join channels c
    on y.channel_name = c.channel_username
left join dates d
    on m.date_key = d.date_key