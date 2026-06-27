"""
Telegram Medical Channel Scraper
Scrapes messages and images from public Ethiopian medical Telegram channels
and stores them in a structured data lake.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# ── Load environment variables ──────────────────────────────────────────────
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# ── Channels to scrape ───────────────────────────────────────────────────────
CHANNELS = [
    "CheMed123",
    "lobelia4cosmetics",
    "tikvahethiopiabot",
    "DoctorsETBot",
    "yetenaweg",
]

# ── Limits ───────────────────────────────────────────────────────────────────
MESSAGE_LIMIT = 200  # messages per channel

# ── Set up logging ───────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def scrape_channel(client, channel_username):
    """Scrape messages and images from a single Telegram channel."""
    logger.info(f"Starting scrape: {channel_username}")
    messages_data = []

    try:
        entity = await client.get_entity(channel_username)
        channel_name = entity.title
        logger.info(f"Connected to channel: {channel_name}")

        async for message in client.iter_messages(entity, limit=MESSAGE_LIMIT):
            # ── Build message record ─────────────────────────────────────
            record = {
                "message_id": message.id,
                "channel_username": channel_username,
                "channel_name": channel_name,
                "message_date": message.date.isoformat() if message.date else None,
                "message_text": message.text or "",
                "has_media": message.media is not None,
                "image_path": None,
                "views": message.views or 0,
                "forwards": message.forwards or 0,
            }

            # ── Download image if present ────────────────────────────────
            if isinstance(message.media, MessageMediaPhoto):
                image_dir = f"data/raw/images/{channel_username}"
                os.makedirs(image_dir, exist_ok=True)
                image_path = f"{image_dir}/{message.id}.jpg"

                try:
                    await client.download_media(message.media, file=image_path)
                    record["image_path"] = image_path
                    logger.info(f"  Downloaded image: {image_path}")
                except Exception as e:
                    logger.error(f"  Failed to download image for message {message.id}: {e}")

            messages_data.append(record)

        logger.info(f"Scraped {len(messages_data)} messages from {channel_name}")

    except Exception as e:
        logger.error(f"Failed to scrape {channel_username}: {e}")

    return messages_data


def save_to_data_lake(channel_username, messages):
    """Save scraped messages to partitioned JSON files in the data lake."""
    if not messages:
        logger.warning(f"No messages to save for {channel_username}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"data/raw/telegram_messages/{today}"
    os.makedirs(output_dir, exist_ok=True)

    output_path = f"{output_dir}/{channel_username}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(messages)} messages to {output_path}")


async def main():
    """Main function — connects to Telegram and scrapes all channels."""
    logger.info("=" * 60)
    logger.info("Telegram Medical Channel Scraper Started")
    logger.info("=" * 60)

    client = TelegramClient("medical_scraper_session", API_ID, API_HASH)

    async with client:
        await client.start(phone=PHONE_NUMBER)
        logger.info("Successfully connected to Telegram")

        for channel in CHANNELS:
            messages = await scrape_channel(client, channel)
            save_to_data_lake(channel, messages)
            logger.info(f"Finished channel: {channel}")
            # Small delay to avoid rate limiting
            await asyncio.sleep(2)

    logger.info("=" * 60)
    logger.info("Scraping Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())