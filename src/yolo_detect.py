"""
YOLOv8 Object Detection Script
Scans downloaded images, runs detection, classifies each image,
and saves results to a CSV file.
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO

# ── Logging setup ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/yolo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
IMAGES_DIR = "data/raw/images"
OUTPUT_CSV = "data/yolo_detections.csv"
CONFIDENCE_THRESHOLD = 0.3

# YOLO classes we care about
PERSON_CLASSES = {"person"}
PRODUCT_CLASSES = {"bottle", "cup", "bowl", "vase", "book", "box",
                   "toothbrush", "scissors", "cell phone", "laptop"}


def classify_image(detected_classes):
    """Classify image based on what objects were detected."""
    has_person = bool(PERSON_CLASSES & detected_classes)
    has_product = bool(PRODUCT_CLASSES & detected_classes)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"


def run_detection():
    """Run YOLOv8 detection on all downloaded images."""
    logger.info("=" * 60)
    logger.info("YOLOv8 Detection Started")
    logger.info("=" * 60)

    # Load model (downloads automatically on first run)
    logger.info("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")
    logger.info("Model loaded successfully")

    results_data = []
    total_images = 0
    processed = 0

    # Count total images first
    for channel_folder in Path(IMAGES_DIR).iterdir():
        if channel_folder.is_dir():
            total_images += len(list(channel_folder.glob("*.jpg")))

    logger.info(f"Found {total_images} images to process")

    # Process each channel folder
    for channel_folder in Path(IMAGES_DIR).iterdir():
        if not channel_folder.is_dir():
            continue

        channel_name = channel_folder.name
        logger.info(f"Processing channel: {channel_name}")

        for image_path in channel_folder.glob("*.jpg"):
            try:
                message_id = image_path.stem

                # Run detection
                results = model(str(image_path), verbose=False,
                                conf=CONFIDENCE_THRESHOLD)

                # Extract detected objects
                detected_classes = set()
                detections = []

                for result in results:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]
                        confidence = float(box.conf[0])
                        detected_classes.add(class_name)
                        detections.append({
                            "class": class_name,
                            "confidence": round(confidence, 3)
                        })

                # Classify image
                image_category = classify_image(detected_classes)

                # Get top detection
                top_class = ""
                top_confidence = 0.0
                if detections:
                    top = max(detections, key=lambda x: x["confidence"])
                    top_class = top["class"]
                    top_confidence = top["confidence"]

                results_data.append({
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "image_path": str(image_path),
                    "detected_class": top_class,
                    "confidence_score": top_confidence,
                    "all_detected_classes": ",".join(detected_classes),
                    "image_category": image_category,
                    "total_detections": len(detections)
                })

                processed += 1
                if processed % 20 == 0:
                    logger.info(f"Progress: {processed}/{total_images} images")

            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")

    # Save results to CSV
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["message_id", "channel_name", "image_path",
                      "detected_class", "confidence_score",
                      "all_detected_classes", "image_category",
                      "total_detections"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_data)

    logger.info("=" * 60)
    logger.info(f"Detection Complete!")
    logger.info(f"Processed: {processed} images")
    logger.info(f"Results saved to: {OUTPUT_CSV}")

    # Print summary
    categories = {}
    for r in results_data:
        cat = r["image_category"]
        categories[cat] = categories.get(cat, 0) + 1

    logger.info("Category breakdown:")
    for cat, count in sorted(categories.items()):
        logger.info(f"  {cat}: {count} images")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_detection()