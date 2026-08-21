from camoufox.sync_api import Camoufox
import os

# Folder where the browser profile will be saved between runs
USER_DATA_DIR = os.path.join(os.getcwd(), "browser_profile")

with Camoufox(headless=False, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    input("Press Enter to close...")