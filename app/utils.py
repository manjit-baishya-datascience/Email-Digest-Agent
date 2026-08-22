import json
from datetime import datetime
import re

def parse_forwarded_header(full_body: str) -> dict:
    """Extracts the original sender/date/subject from a forwarded
    email's embedded header block. Returns None for any field it
    can't find, rather than guessing."""

    from_match = re.search(r"From:\s*(.+?)\s*<(.+?)>", full_body)
    date_match = re.search(r"Date:\s*(.+)", full_body)
    subject_match = re.search(r"Subject:\s*(.+)", full_body)

    sender_name = from_match.group(1).strip() if from_match else None
    sender_email = from_match.group(2).strip() if from_match else None
    original_date = date_match.group(1).strip() if date_match else None
    original_subject = subject_match.group(1).strip() if subject_match else None

    # Body = whatever comes after the "Subject:" line and the "To:" line
    # that typically follows it — everything past the header block
    body_start = full_body.find("\n", full_body.find("Subject:"))
    original_body = full_body[body_start:].strip() if body_start != -1 else None

    return {
        "sender_name": sender_name,
        "sender_email": sender_email,
        "date_time": original_date,
        "subject": original_subject,
        "body": original_body
    }

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