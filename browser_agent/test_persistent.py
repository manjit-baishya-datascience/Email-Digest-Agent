from camoufox.sync_api import Camoufox
import os
import time

USER_DATA_DIR = os.path.join(os.getcwd(), "browser_profile")
print(f"Using profile dir: {USER_DATA_DIR}")

with Camoufox(headless=False, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
    page = browser.new_page()
    page.goto("https://example.com")

    cookies = page.context.cookies()
    test_cookie = next((c for c in cookies if c["name"] == "my_test_cookie"), None)

    if test_cookie:
        print(f"FOUND EXISTING COOKIE! Value: {test_cookie['value']}")
    else:
        print("No existing cookie found — setting one now for next time.")
        page.context.add_cookies([{
            "name": "my_test_cookie",
            "value": "hello_from_run_1",
            "domain": "example.com",
            "path": "/",
            "expires": time.time() + 86400  # expires 1 day from now, not a session cookie
        }])

    print("Closing now...")

print("Script fully exited.")