from camoufox.sync_api import Camoufox
from config import USER_DATA_DIR
import json
import os
from datetime import datetime

with Camoufox(headless=False, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
    if browser.pages:
        page = browser.pages[0]
    else:
        page = browser.new_page()

    page.goto("https://outlook.com")
    page.wait_for_selector('[role="complementary"][aria-label="Message list"]')

    rows = page.locator('[role="option"]')
    count = rows.count()
    print(f"Found {count} emails")

    emails = []
    for i in range(count):
        label = rows.nth(i).get_attribute("aria-label")
        emails.append({
            "index": i + 1,
            "raw_label": label
        })

    # Make sure an output folder exists
    os.makedirs("scraped_data", exist_ok=True)

    # Timestamped filename so each run is kept separately
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"scraped_data/inbox_{timestamp}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)

    print(f"Saved {count} emails to {filepath}")

    input("\nPress Enter to close...")