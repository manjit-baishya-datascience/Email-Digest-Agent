import json
from datetime import datetime


def strip_json_fences(raw_text: str) -> str:
    """Ollama sometimes wraps JSON output in ```json ... ``` fences despite
    being instructed not to. Strip them if present, otherwise return
    the text unchanged."""
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

    return cleaned.strip()


def is_forwarded_message(raw_label: str) -> bool:
    """Detects whether a scraped message row represents a forwarded
    email, based on the marker Outlook inserts into forwarded content."""
    return "Forwarded message" in raw_label


def timestamped_filename(prefix: str, extension: str) -> str:
    """Builds a filename like 'digest_20260822_143000.md' so repeated
    runs don't overwrite each other's output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"