"""
Dagster Pipeline Orchestration
Orchestrates the full medical telegram data pipeline.
"""

import subprocess
import os
from dagster import op, job, OpExecutionContext, ScheduleDefinition, Definitions, In, Nothing, graph

@op
def scrape_telegram_data(context: OpExecutionContext):
    """Scrapes messages and images from Telegram channels."""
    context.log.info("Starting Telegram scraping...")
    result = subprocess.run(
        ["python", "src/scraper.py"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Scraper failed: {result.stderr}")
    context.log.info("Scraping complete!")

@op(ins={"start": In(Nothing)})
def load_raw_to_postgres(context: OpExecutionContext):
    """Loads raw JSON files into PostgreSQL."""
    context.log.info("Loading raw data to PostgreSQL...")
    result = subprocess.run(
        ["python", "scripts/load_to_postgres.py"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Load failed: {result.stderr}")
    context.log.info("Raw data loaded!")

@op(ins={"start": In(Nothing)})
def run_dbt_transformations(context: OpExecutionContext):
    """Runs dbt models to transform data into star schema."""
    context.log.info("Running dbt transformations...")
    result = subprocess.run(
        ["dbt", "run"],
        capture_output=True, text=True,
        cwd=os.path.join(os.getcwd(), "medical_warehouse")
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt failed: {result.stderr}")
    context.log.info("Running dbt tests...")
    subprocess.run(["dbt", "test"], cwd=os.path.join(os.getcwd(), "medical_warehouse"))
    context.log.info("dbt complete!")

@op(ins={"start": In(Nothing)})
def run_yolo_enrichment(context: OpExecutionContext):
    """Runs YOLOv8 object detection on downloaded images."""
    context.log.info("Running YOLO enrichment...")
    result = subprocess.run(
        ["python", "src/yolo_detect.py"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"YOLO failed: {result.stderr}")
    subprocess.run(["python", "scripts/load_yolo_to_postgres.py"], cwd=os.getcwd())
    context.log.info("YOLO enrichment complete!")

@job
def medical_telegram_pipeline():
    """Full end-to-end medical telegram data pipeline."""
    scrape = scrape_telegram_data()
    load = load_raw_to_postgres(start=scrape)
    dbt = run_dbt_transformations(start=load)
    run_yolo_enrichment(start=dbt)

daily_schedule = ScheduleDefinition(
    job=medical_telegram_pipeline,
    cron_schedule="0 6 * * *",
)

defs = Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_schedule],
)