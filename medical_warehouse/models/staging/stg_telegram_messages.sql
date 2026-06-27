-- Staging model: cleans and standardizes raw telegram messages

with source as (
    select * from raw.telegram_messages
),

cleaned as (
    select
        message_id::integer                          as message_id,
        channel_username                             as channel_username,
        channel_name                                 as channel_name,
        message_date::timestamptz                    as message_date,
        message_date::date                           as message_date_day,
        message_text                                 as message_text,
        length(message_text)                         as message_length,
        has_media::boolean                           as has_media,
        case
            when image_path is not null
            and image_path != '' then true
            else false
        end                                          as has_image,
        image_path                                   as image_path,
        views::integer                               as views,
        forwards::integer                            as forwards
    from source
    where message_text is not null
      and message_text != ''
      and message_date is not null
)

select * from cleaned