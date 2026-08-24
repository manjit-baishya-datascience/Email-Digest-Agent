import os
import logging
from datetime import datetime
from app.config import OUTPUTS_DIR
from app.exceptions import PersistenceError
from app.utils import timestamped_filename

logger = logging.getLogger(__name__)


def format_digest_markdown(digest_items: list[dict], overview: str = "") -> str:
    """Formats digest items into a human-readable Markdown document.
    Pure function — takes structured data, returns a string, no disk
    access — testable without ever writing a file. digest_items is
    already filtered to urgent-only and sorted by urgency (highest
    first) by summarize_emails, so no re-sorting or re-filtering
    happens here."""

    lines = [f"# Urgent Email Digest — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]

    if not digest_items:
        lines.append("No emails met the urgency threshold in this run.\n")
        return "\n".join(lines)

    if overview:
        lines.append("## Overview\n")
        lines.append(f"{overview}\n")

    lines.append(f"## {len(digest_items)} Urgent Message(s)\n")

    for item in digest_items:
        lines.append(f"### {item['subject']}")
        lines.append(f"- **From:** {item['sender']} <{item['sender_email']}>")
        lines.append(f"- **Date:** {item['date_time']}")
        lines.append(f"- **Urgency:** {item['urgency_score']}/5")
        lines.append(f"- **Summary:** {item['summary']}")
        lines.append("")

    return "\n".join(lines)


def save_digest(digest_items: list[dict], overview: str = "") -> str:
    """Formats and writes the digest to a timestamped Markdown file in
    OUTPUTS_DIR. Returns the path written. Raises PersistenceError if
    the write fails."""

    content = format_digest_markdown(digest_items, overview)

    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        filename = timestamped_filename("digest", "md")
        filepath = os.path.join(OUTPUTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Digest saved to {filepath}")
        return filepath

    except OSError as e:
        raise PersistenceError(f"Failed to write digest file: {e}") from e