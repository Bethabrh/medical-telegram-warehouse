"""
Loads YOLO detection results CSV into PostgreSQL
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def load_yolo_results():
    engine = create_engine(DATABASE_URL)

    df = pd.read_csv("data/yolo_detections.csv")
    df["message_id"] = df["message_id"].astype(str)
    df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce").fillna(0.0)
    df["total_detections"] = pd.to_numeric(df["total_detections"], errors="coerce").fillna(0).astype(int)

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()

    df.to_sql(
        name="yolo_detections",
        schema="raw",
        con=engine,
        if_exists="replace",
        index=False
    )

    print(f"Loaded {len(df)} rows into raw.yolo_detections")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT image_category, COUNT(*) FROM raw.yolo_detections GROUP BY image_category ORDER BY COUNT(*) DESC"))
        print("\nCategory breakdown in database:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    print("Loading YOLO results to PostgreSQL...")
    load_yolo_results()
    print("Done!")