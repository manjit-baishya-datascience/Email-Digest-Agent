import sys
import os
import json
import glob

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import logging
logging.basicConfig(level=logging.INFO)

from app.digest import save_digest, format_digest_markdown, sort_by_urgency


def find_latest_summary_file() -> str:
    """Finds the most recently modified JSON file in scraped_data/
    whose filename contains 'summarizer', so this test always runs
    against your latest real digest items without needing to hardcode
    an exact filename."""
    pattern = os.path.join(PROJECT_ROOT, "scraped_data", "*summarizer*.json")
    files = glob.glob(pattern)

    if not files:
        raise FileNotFoundError(
            f"No summarizer output files found matching {pattern}. "
            f"Run scripts/summarizer_manual_test.py first to generate one."
        )

    latest = max(files, key=os.path.getmtime)
    return latest


if __name__ == "__main__":
    summary_file = find_latest_summary_file()
    print(f"Using digest items from: {summary_file}\n")

    with open(summary_file, "r", encoding="utf-8") as f:
        digest_items = json.load(f)

    print(f"Loaded {len(digest_items)} digest items\n")

    # Quick sanity check on sorting, before writing anything to disk
    sorted_items = sort_by_urgency(digest_items)
    print("Order after sorting by urgency (highest first):")
    for item in sorted_items:
        print(f"  [{item.get('urgency_score')}] {item.get('subject')}")
    print()

    # Preview the formatted Markdown in the terminal before saving
    markdown_preview = format_digest_markdown(digest_items)
    print("--- Markdown preview ---\n")
    print(markdown_preview)
    print("\n--- end preview ---\n")

    # Now actually write it to disk via the real save function
    output_path = save_digest(digest_items)
    print(f"Digest written to: {output_path}")
    print("Open it in VS Code and preview with Ctrl+Shift+V to check formatting.")