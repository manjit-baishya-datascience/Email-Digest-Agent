import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from camoufox.sync_api import Camoufox
from app.config import USER_DATA_DIR, OUTLOOK_INBOX_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # If a session was already saved before, USER_DATA_DIR will exist on
    # disk and Camoufox will load it automatically — no extra logic needed,
    # this check just tells us what to expect/log.
    session_exists = os.path.isdir(USER_DATA_DIR) and len(os.listdir(USER_DATA_DIR)) > 0

    with Camoufox(headless=False, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(OUTLOOK_INBOX_URL)

        if session_exists:
            logger.info("Existing session found — should be logged in automatically.")
        else:
            logger.info("No existing session found. Please log in manually (including 2FA).")

        input("Press Enter once you can see your inbox...")
        logger.info("Session saved for future automated runs.")

if __name__ == "__main__":
    main()