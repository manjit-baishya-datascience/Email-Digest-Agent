import sys
import os
import csv
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from app.summarizer import build_prompt

INPUT_PATH = "finetune_data/labelled_dataset.csv"
OUTPUT_PATH = "finetune_data/training_data.jsonl"

def row_to_training_example(row: dict) -> dict:
    """Builds one training example using the same prompt structure the
    real summarizer.py uses at inference time, paired with the
    human-labeled correct output."""

    fake_email_dict = {
        "is_forwarded": False,
        "body": row["body"]
    }

    prompt = build_prompt(fake_email_dict)

    needs_action = str(row.get("needs_action", "")).strip().lower() in ("yes", "true", "1")

    try:
        urgency_score = int(row.get("urgency_score", "1"))
    except ValueError:
        urgency_score = 1

    completion = json.dumps({
        "summary": row.get("summary", "").strip(),
        "needs_action": needs_action,
        "urgency_score": urgency_score,
        "priority_reason": row.get("priority_reason", "").strip(),
        "dates_mentioned": row.get("dates_mentioned", "none").strip() or "none"
    })

    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": completion}
        ]
    }

if __name__ == "__main__":
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} labeled rows")

    skipped = 0
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for i, row in enumerate(rows):
            if not row.get("body", "").strip():
                print(f"Row {i + 1}: empty body, skipping")
                skipped += 1
                continue
            if not row.get("urgency_score", "").strip():
                print(f"Row {i + 1}: missing urgency_score, skipping")
                skipped += 1
                continue

            example = row_to_training_example(row)
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    written = len(rows) - skipped
    print(f"\nWrote {written} training examples to {OUTPUT_PATH} ({skipped} skipped)")