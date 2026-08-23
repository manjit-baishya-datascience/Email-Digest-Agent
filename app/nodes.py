import logging
from app.state import AgentState
from app.scraper import scrape_inbox
from app.summarizer import summarize_emails
from app.digest import save_digest
from app.exceptions import ScrapingError, LLMError, PersistenceError

logger = logging.getLogger(__name__)


def scrape_node(state: AgentState) -> dict:
    """Scrapes the inbox. On failure, captures the error in state
    rather than raising, so the graph can route to error handling
    instead of crashing the whole run."""
    try:
        emails = scrape_inbox()
        logger.info(f"scrape_node: collected {len(emails)} emails")
        return {"emails": emails}
    except ScrapingError as e:
        logger.error(f"scrape_node failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


def summarize_node(state: AgentState) -> dict:
    """Summarizes previously scraped emails. Skips work if an earlier
    node already failed, so a broken pipeline doesn't try to summarize
    data that was never scraped."""
    if state.get("error"):
        return {}

    try:
        digest_items = summarize_emails(state["emails"])
        logger.info(f"summarize_node: produced {len(digest_items)} digest items")
        return {"digest_items": digest_items}
    except LLMError as e:
        logger.error(f"summarize_node failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


def save_node(state: AgentState) -> dict:
    """Saves the digest to disk. Skips work if an earlier node already
    failed."""
    if state.get("error"):
        return {}

    try:
        output_path = save_digest(state["digest_items"])
        logger.info(f"save_node: digest saved to {output_path}")
        return {"output_path": output_path}
    except PersistenceError as e:
        logger.error(f"save_node failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}


def error_node(state: AgentState) -> dict:
    """Terminal node reached when any prior stage failed. Logs the
    failure clearly; the graph ends here rather than continuing with
    incomplete data."""
    logger.error(
        f"Pipeline failed at stage producing error_type="
        f"{state.get('error_type')}: {state.get('error')}"
    )
    return {}