"""
Medical Telegram Warehouse - Analytical API
Exposes cleaned warehouse data through REST endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from api.database import get_db
from api import schemas

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="Analytical API for Ethiopian medical Telegram channel data",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Medical Telegram Warehouse API", "status": "running"}


@app.get("/api/reports/top-products", response_model=List[schemas.TopProduct])
def get_top_products(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns the most frequently mentioned words across all channels."""
    query = text("""
        SELECT word, COUNT(*) as frequency
        FROM (
            SELECT regexp_split_to_table(
                lower(message_text), '\\s+'
            ) as word
            FROM public_marts.fct_messages
            WHERE message_text IS NOT NULL
              AND length(message_text) > 0
        ) words
        WHERE length(word) > 3
          AND word NOT IN ('this','that','with','from','have','will',
                           'your','they','been','were','what','when',
                           'which','there','their','about','would')
        GROUP BY word
        ORDER BY frequency DESC
        LIMIT :limit
    """)
    results = db.execute(query, {"limit": limit}).fetchall()
    return [{"word": row[0], "frequency": row[1]} for row in results]


@app.get("/api/channels/{channel_name}/activity",
         response_model=schemas.ChannelActivity)
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """Returns posting activity and engagement stats for a specific channel."""
    query = text("""
        SELECT
            c.channel_name,
            c.channel_type,
            c.total_posts,
            c.avg_views,
            c.first_post_date::text,
            c.last_post_date::text
        FROM public_marts.dim_channels c
        WHERE lower(c.channel_username) = lower(:channel_name)
           OR lower(c.channel_name) = lower(:channel_name)
    """)
    result = db.execute(query, {"channel_name": channel_name}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {
        "channel_name": result[0],
        "channel_type": result[1],
        "total_posts": result[2],
        "avg_views": float(result[3]),
        "first_post_date": result[4],
        "last_post_date": result[5]
    }


@app.get("/api/search/messages", response_model=List[schemas.MessageResult])
def search_messages(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search for messages containing a specific keyword."""
    sql = text("""
        SELECT
            f.message_id,
            c.channel_name,
            f.message_text,
            f.views,
            f.forwards,
            f.has_image
        FROM public_marts.fct_messages f
        JOIN public_marts.dim_channels c ON f.channel_key = c.channel_key
        WHERE lower(f.message_text) LIKE lower(:query)
        ORDER BY f.views DESC
        LIMIT :limit
    """)
    results = db.execute(sql, {
        "query": f"%{query}%",
        "limit": limit
    }).fetchall()
    return [
        {
            "message_id": row[0],
            "channel_name": row[1],
            "message_text": row[2],
            "views": row[3],
            "forwards": row[4],
            "has_image": row[5]
        }
        for row in results
    ]


@app.get("/api/reports/visual-content",
         response_model=List[schemas.VisualContentStat])
def get_visual_content_stats(db: Session = Depends(get_db)):
    """Returns image usage statistics across all channels."""
    query = text("""
        SELECT
            i.channel_name,
            COUNT(*) as total_images,
            SUM(CASE WHEN i.image_category = 'promotional' THEN 1 ELSE 0 END) as promotional,
            SUM(CASE WHEN i.image_category = 'product_display' THEN 1 ELSE 0 END) as product_display,
            SUM(CASE WHEN i.image_category = 'lifestyle' THEN 1 ELSE 0 END) as lifestyle,
            SUM(CASE WHEN i.image_category = 'other' THEN 1 ELSE 0 END) as other
        FROM public_marts.fct_image_detections i
        GROUP BY i.channel_name
        ORDER BY total_images DESC
    """)
    results = db.execute(query).fetchall()
    return [
        {
            "channel_name": row[0],
            "total_images": row[1],
            "promotional": row[2],
            "product_display": row[3],
            "lifestyle": row[4],
            "other": row[5]
        }
        for row in results
    ]