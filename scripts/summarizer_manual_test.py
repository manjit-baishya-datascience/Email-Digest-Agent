import sys
import os
import json
import glob

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import logging
logging.basicConfig(level=logging.INFO)

from app.summarizer import summarize_emails

def find_latest_scrape_file() -> str:
    """Finds the most recently modified JSON file in scraped_data/,
    so this test always runs against your latest real scrape without
    needing to hardcode a filename."""
    pattern = os.path.join(PROJECT_ROOT, "scraped_data", "*.json")
    files = glob.glob(pattern)

    if not files:
        raise FileNotFoundError(
            f"No scraped JSON files found in {os.path.join(PROJECT_ROOT, 'scraped_data')}. "
            f"Run scripts/scraper_manual_test.py first to generate one."
        )

    latest = max(files, key=os.path.getmtime)
    return latest

if __name__ == "__main__":
    scrape_file = find_latest_scrape_file()
    print(f"Using scraped data from: {scrape_file}\n")

    with open(scrape_file, "r", encoding="utf-8") as f:
        emails = json.load(f)

    print(f"Loaded {len(emails)} emails\n")

    digest_items = summarize_emails(emails)

    print(f"\nSummarization produced {len(digest_items)} digest items\n")

    for item in digest_items:
        print(f"--- {item.get('subject')} ---")
        print(f"  Sender: {item.get('sender')}")
        print(f"  Urgency: {item.get('urgency_score')} — {item.get('priority_reason')}")
        print(f"  Needs action: {item.get('needs_action')}")
        print(f"  Dates mentioned: {item.get('dates_mentioned')}")
        print(f"  Summary: {item.get('summary')}")
        print()

    # Save output for inspection
    output_dir = os.path.join(PROJECT_ROOT, "scraped_data")
    output_path = os.path.join(output_dir, "summarizer_test_output.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(digest_items, f, indent=2, ensure_ascii=False)

    print(f"Full output saved to {output_path}")