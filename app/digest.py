import os
import logging
from datetime import datetime
from app.config import OUTPUTS_DIR
from app.exceptions import PersistenceError
from app.utils import timestamped_filename

logger = logging.getLogger(__name__)

def sort_by_urgency(digest_items: list[dict]) -> list[dict]:
    """Returns digest items sorted by urgency_score, highest first.
    Pure function — no side effects — easy to unit test directly."""
    return sorted(digest_items, key=lambda item: item.get("urgency_score", 1), reverse=True)

def format_digest_markdown(digest_items: list[dict]) -> str:
    """Formats digest items into a human-readable Markdown document.
    Pure function — takes structured data, returns a string, no disk
    access — testable without ever writing a file."""

    lines = [f"# Inbox Digest — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]

    if not digest_items:
        lines.append("No emails were found or summarized in this run.\n")
        return "\n".join(lines)

    sorted_items = sort_by_urgency(digest_items)

    action_items = [item for item in sorted_items if item.get("needs_action")]
    if action_items:
        lines.append("## ⚠️ Needs Action\n")
        for item in action_items:
            lines.append(
                f"- **{item['subject']}** (from {item['sender']}, urgency {item['urgency_score']}/5) "
                f"— {item['summary']}"
            )
        lines.append("")

    lines.append("## All Messages (by urgency)\n")
    for item in sorted_items:
        lines.append(f"### {item['subject']}")
        lines.append(f"- **From:** {item['sender']} <{item['sender_email']}>")
        lines.append(f"- **Date:** {item['date_time']}")
        lines.append(f"- **Summary:** {item['summary']}")
        lines.append(f"- **Urgency:** {item['urgency_score']}/5 — {item['priority_reason']}")
        lines.append(f"- **Needs action:** {item['needs_action']}")
        lines.append(f"- **Needs attention:** {item['needs_attention']}")
        lines.append(f"- **Dates mentioned:** {item['dates_mentioned']}")
        lines.append("")

    return "\n".join(lines)

def save_digest(digest_items: list[dict]) -> str:
    """Formats and writes the digest to a timestamped Markdown file in
    OUTPUTS_DIR. Returns the path written. Raises PersistenceError if
    the write fails."""

    content = format_digest_markdown(digest_items)

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