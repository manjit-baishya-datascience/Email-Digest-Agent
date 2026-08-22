import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
logging.basicConfig(level=logging.INFO)

from app.scraper import scrape_inbox
import json

if __name__ == "__main__":
    emails = scrape_inbox()

    print(f"\nScraped {len(emails)} emails\n")

    # for e in emails:
    #     print(f"--- Email {e['index']} (forwarded: {e['is_forwarded']}) ---")
    #     print(f"Message ID: {e['message_id']}")
    #     print(f"Sender: {e['sender_name']} <{e['sender_email']}>")
    #     print(f"Subject: {e['subject']}")
    #     print(f"Date/Time: {e['date_time']}")
    #     body_preview = (e['body'] or "NONE")[:150]
    #     print(f"Body preview: {body_preview}")
    #     print()

    # Also save full output so you can inspect it properly in a file
    with open("scraped_data/scraper_test_output.json", "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)

    print("Full output saved to scraped_data/scraper_test_output.json")