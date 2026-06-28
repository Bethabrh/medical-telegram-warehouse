from pydantic import BaseModel
from typing import Optional, List

class TopProduct(BaseModel):
    word: str
    frequency: int

class ChannelActivity(BaseModel):
    channel_name: str
    channel_type: str
    total_posts: int
    avg_views: float
    first_post_date: Optional[str]
    last_post_date: Optional[str]

class MessageResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: str
    views: int
    forwards: int
    has_image: bool

class VisualContentStat(BaseModel):
    channel_name: str
    total_images: int
    promotional: int
    product_display: int
    lifestyle: int
    other: int

class DetectionStat(BaseModel):
    image_category: str
    count: int
    avg_views: Optional[float]