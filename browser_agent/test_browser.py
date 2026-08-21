from camoufox.sync_api import Camoufox

with Camoufox(headless=False) as browser:
    page = browser.new_page()
    page.goto("https://www.google.com")
    print(page.title())
    input("Press Enter to close the browser...")