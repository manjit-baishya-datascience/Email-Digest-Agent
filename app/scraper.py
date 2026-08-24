import re
import logging
from camoufox.sync_api import Camoufox
from app.config import USER_DATA_DIR, OUTLOOK_INBOX_URL, MESSAGE_LIST_TIMEOUT_MS
from app.exceptions import ScrapingError
from app.utils import is_forwarded_message, parse_forwarded_header

logger = logging.getLogger(__name__)

TARGET_EMAIL_COUNT = 15
MAX_SCROLL_ATTEMPTS = 10
SCROLL_PAUSE_MS = 500

SCROLLER_SELECTOR = '[data-testid="virtuoso-scroller"]'
ROW_SELECTOR = '[role="option"]'
SUBJECT_SELECTOR = ".TtcXM"
BODY_SELECTOR = ".ASFJj"

def extract_shallow_fields(row, index: int) -> dict:
    """Extracts the 6-field schema directly from a message row's DOM,
    for a non-forwarded email. Selectors confirmed via live DevTools
    console inspection. Returns None for any field that can't be
    found rather than guessing."""

    message_id = row.get_attribute("data-convid")

    titled_spans = row.locator("span[title]")
    sender_email = titled_spans.first.get_attribute("title") if titled_spans.count() > 0 else None
    sender_name = titled_spans.first.inner_text() if titled_spans.count() > 0 else None
    date_time = titled_spans.last.get_attribute("title") if titled_spans.count() > 0 else None

    subject_el = row.locator(SUBJECT_SELECTOR)
    subject = subject_el.inner_text() if subject_el.count() > 0 else None

    body_el = row.locator(BODY_SELECTOR)
    body = body_el.inner_text() if body_el.count() > 0 else None

    return {
        "message_id": message_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": subject,
        "date_time": date_time,
        "body": body,
        "is_forwarded": False,
        "index": index
    }

def scrape_deep(page, row, index: int) -> dict:
    message_id = row.get_attribute("data-convid")

    row.click()
    page.wait_for_selector('[role="document"]', timeout=MESSAGE_LIST_TIMEOUT_MS)
    full_body = page.locator('[role="document"]').first.inner_text()

    parsed = parse_forwarded_header(full_body)

    # Return to the inbox list view before continuing to scan other
    # rows — clicking into an email can leave the virtualized list in
    # an unstable state otherwise.
    page.go_back()
    page.wait_for_selector('[role="complementary"][aria-label="Message list"]', timeout=MESSAGE_LIST_TIMEOUT_MS)

    return {
        "message_id": message_id,
        "sender_name": parsed["sender_name"],
        "sender_email": parsed["sender_email"],
        "subject": parsed["subject"],
        "date_time": parsed["date_time"],
        "body": parsed["body"],
        "is_forwarded": True,
        "index": index
    }

def scroll_and_collect_emails(page, target_count: int = TARGET_EMAIL_COUNT,
                               max_scroll_attempts: int = MAX_SCROLL_ATTEMPTS) -> list[dict]:
    """Scrolls the virtualized message list (react-virtuoso) while
    extracting data at each step, since scrolled-out rows are
    destroyed from the DOM and cannot be read after the fact.
    Accumulates unique messages by message_id until target_count is
    reached or the list stops producing new messages. A single row's
    failure (timeout, DOM instability from virtualization) is logged
    and skipped rather than aborting the entire scrape."""

    scroller = page.locator(SCROLLER_SELECTOR)
    collected = {}  # keyed by message_id to avoid duplicates across scroll steps

    for attempt in range(max_scroll_attempts):
        rows = page.locator(ROW_SELECTOR)
        row_count = rows.count()

        for i in range(row_count):
            try:
                row = rows.nth(i)
                message_id = row.get_attribute("data-convid")

                if message_id in collected:
                    continue  # already captured this one on a previous scroll step

                raw_label = row.get_attribute("aria-label") or ""

                if is_forwarded_message(raw_label):
                    try:
                        email = scrape_deep(page, row, len(collected) + 1)
                        logger.info(
                            f"Forwarded message resolved — original sender: "
                            f"{email['sender_name']} <{email['sender_email']}>"
                        )
                    except Exception as e:
                        logger.warning(f"Deep scrape failed for message {message_id}: {e}")
                        email = extract_shallow_fields(row, len(collected) + 1)
                        email["is_forwarded"] = True
                else:
                    email = extract_shallow_fields(row, len(collected) + 1)

                collected[message_id] = email

                if len(collected) >= target_count:
                    logger.info(f"Reached target of {target_count} messages")
                    return list(collected.values())

            except Exception as e:
                logger.warning(f"Skipping row {i} entirely — failed to read: {e}")
                continue

        # Scroll for more, then check whether anything new actually loaded
        previous_total = len(collected)
        scroller.evaluate("el => el.scrollTop = el.scrollHeight")
        page.wait_for_timeout(SCROLL_PAUSE_MS)

        if len(collected) == previous_total and attempt > 0:
            logger.info(f"No new messages after scrolling — reached end of inbox at {len(collected)}")
            break

    return list(collected.values())

def scrape_inbox() -> list[dict]:
    """Full scraping pipeline: launches the browser, scrolls the
    virtualized inbox list while extracting each message's 6-field
    schema (shallow for native messages, deep + parsed for forwarded
    ones). Raises ScrapingError on failure, with a specific message
    describing what went wrong."""

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

            emails = scroll_and_collect_emails(page)
            logger.info(f"Scraping complete — {len(emails)} messages collected")
            return emails

    except ScrapingError:
        raise
    except Exception as e:
        raise ScrapingError(f"Unexpected scraping failure: {e}") from e