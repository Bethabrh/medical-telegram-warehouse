# Medical Telegram Warehouse

End-to-end data pipeline for Ethiopian medical Telegram channels.

## Project Structure
- `src/scraper.py` — Telegram scraper using Telethon
- `scripts/load_to_postgres.py` — Loads raw JSON into PostgreSQL
- `medical_warehouse/` — dbt project with staging and mart models

## Data Pipeline
1. Scrape messages from public Telegram channels
2. Store raw JSON in partitioned data lake
3. Load
