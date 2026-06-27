"""
Loads raw JSON files from the data lake into PostgreSQL
raw schema as the telegram_messages table.
"""

import os
import json
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote_plus

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

from urllib.parse import quote_plus
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def load_json_files():
    """Read all JSON files from the data lake."""
    all_messages = []
    base_path = "data/raw/telegram_messages"

    for date_folder in os.listdir(base_path):
        date_path = os.path.join(base_path, date_folder)
        if os.path.isdir(date_path):
            for json_file in os.listdir(date_path):
                if json_file.endswith(".json"):
                    file_path = os.path.join(date_path, json_file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        messages = json.load(f)
                        all_messages.extend(messages)
                    print(f"Loaded {len(messages)} messages from {json_file}")

    print(f"\nTotal messages loaded: {len(all_messages)}")
    return all_messages


def load_to_postgres(messages):
    """Load messages into PostgreSQL raw schema."""
    engine = create_engine(DATABASE_URL)

    # Create raw schema
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()
        print("Created raw schema")

    # Convert to DataFrame
    df = pd.DataFrame(messages)

    # Clean up data types
    df["message_date"] = pd.to_datetime(df["message_date"], utc=True)
    df["views"] = pd.to_numeric(df["views"], errors="coerce").fillna(0).astype(int)
    df["forwards"] = pd.to_numeric(df["forwards"], errors="coerce").fillna(0).astype(int)
    df["has_media"] = df["has_media"].astype(bool)
    df["message_text"] = df["message_text"].fillna("")
    df["image_path"] = df["image_path"].fillna("")

    # Load to PostgreSQL
    df.to_sql(
        name="telegram_messages",
        schema="raw",
        con=engine,
        if_exists="replace",
        index=False
    )

    print(f"Successfully loaded {len(df)} rows into raw.telegram_messages")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM raw.telegram_messages"))
        count = result.scalar()
        print(f"Verified: {count} rows in database")


if __name__ == "__main__":
    print("=" * 50)
    print("Loading data to PostgreSQL")
    print("=" * 50)
    messages = load_json_files()
    load_to_postgres(messages)
    print("=" * 50)
    print("Done!")
    print("=" * 50)