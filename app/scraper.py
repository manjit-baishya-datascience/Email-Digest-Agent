import logging
from camoufox.sync_api import Camoufox
from app.config import USER_DATA_DIR, OUTLOOK_INBOX_URL, MESSAGE_LIST_TIMEOUT_MS
from app.exceptions import ScrapingError
from app.utils import is_forwarded_message

logger = logging.getLogger(__name__)


def scrape_shallow(page) -> list[dict]:
    """Extracts sender/subject/snippet directly from each message row's
    aria-label — fast, works for native (non-forwarded) messages."""
    rows = page.locator('[role="option"]')
    count = rows.count()
    logger.info(f"Found {count} messages in inbox")

    emails = []
    for i in range(count):
        label = rows.nth(i).get_attribute("aria-label")
        emails.append({
            "index": i + 1,
            "raw_label": label,
            "is_forwarded": is_forwarded_message(label),
            "full_body": None  # populated later for forwarded messages
        })

    return emails


def scrape_deep(page, email: dict) -> str:
    """Clicks into a single message and extracts the full body text
    from the reading pane. Used only for forwarded messages, where the
    list-row preview is often truncated before the useful content."""
    rows = page.locator('[role="option"]')
    row = rows.nth(email["index"] - 1)
    row.click()

    # Wait for the reading pane to load the opened message's content
    page.wait_for_selector('[role="document"]', timeout=MESSAGE_LIST_TIMEOUT_MS)

    body_element = page.locator('[role="document"]').first
    return body_element.inner_text()


def scrape_inbox() -> list[dict]:
    """Full scraping pipeline: launches the browser, extracts all
    messages (shallow), then deep-extracts any forwarded ones.
    Raises ScrapingError on any failure, with a specific message."""

    try:
        with Camoufox(headless=True, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
            page = browser.pages[0] if browser.pages else browser.new_page()
    except Exception as e:
        raise ScrapingError(f"Browser failed to launch: {e}") from e

    try:
        with Camoufox(headless=True, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto(OUTLOOK_INBOX_URL)

            try:
                page.wait_for_selector(
                    '[role="complementary"][aria-label="Message list"]',
                    timeout=MESSAGE_LIST_TIMEOUT_MS
                )
            except Exception as e:
                raise ScrapingError(
                    f"Message list did not load within {MESSAGE_LIST_TIMEOUT_MS}ms — "
                    f"session may have expired. Run scripts/login_setup.py to re-authenticate."
                ) from e

            emails = scrape_shallow(page)

            forwarded_count = sum(1 for e in emails if e["is_forwarded"])
            logger.info(f"{forwarded_count} forwarded messages detected — fetching full body for each")

            for email in emails:
                if email["is_forwarded"]:
                    try:
                        email["full_body"] = scrape_deep(page, email)
                    except Exception as e:
                        logger.warning(f"Deep scrape failed for email {email['index']}: {e}")
                        # Don't fail the whole run over one message — fall back
                        # to the shallow (possibly truncated) data for this one.
                        email["full_body"] = None

            return emails

    except ScrapingError:
        raise  # already a well-formed ScrapingError, pass it through unchanged
    except Exception as e:
        raise ScrapingError(f"Unexpected scraping failure: {e}") from e