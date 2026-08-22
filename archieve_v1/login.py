from camoufox.sync_api import Camoufox
import os

USER_DATA_DIR = os.path.join(os.getcwd(), "outlook_profile")
with Camoufox(headless=False, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
    page = browser.new_page()
    page.goto("https://outlook.com")
    input("Press Enter to close the browser...")