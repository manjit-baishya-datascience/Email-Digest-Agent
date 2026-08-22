import json
import logging
import ollama
from app.config import LLM_MODEL
from app.exceptions import LLMError
from app.utils import strip_json_fences

logger = logging.getLogger(__name__)

def build_prompt(emails: list[dict]) -> str:
    """Constructs the summarization prompt from clean, structured email
    data. Pure function — no LLM call, no side effects — easy to unit
    test independently of Ollama being available."""

    email_blocks = []
    for e in emails:
        block = (
            f"Message ID: {e['message_id']}\n"
            f"From: {e['sender_name']} <{e['sender_email']}>\n"
            f"Subject: {e['subject']}\n"
            f"Date/Time: {e['date_time']}\n"
            f"Forwarded: {e['is_forwarded']}\n"
            f"Body: {e['body']}"
        )
        email_blocks.append(block)

    emails_text = "\n\n---\n\n".join(email_blocks)

    return f"""You are an email assistant. Below are structured emails scraped from an inbox.
Note: some emails are self-forwarded copies (Forwarded: True) — for these, the sender/subject/
date/body already reflect the ORIGINAL message, not the forwarding. Judge priority based on the
email's content and stated urgency, not on how or when it was delivered to this inbox, since
every email here was manually forwarded by the same person.

For each email, extract and return:
- message_id: copy exactly from the input
- sender: the sender name
- subject: the subject line
- summary: a one-line summary of the email
- needs_action: true or false, whether a response or action is required
- urgency_score: an integer from 1 (no urgency) to 5 (highly urgent), based only on content
- priority_reason: a short phrase explaining the urgency_score
- dates_mentioned: any specific dates mentioned in the body, or "none" if there are none

Only use information present in the text. Do not guess or invent details that are not there.
If something is unclear or missing, say "unknown" rather than guessing.

Respond ONLY with valid JSON, no preamble, no markdown fences, in this exact format:
[
  {{
    "message_id": "...",
    "sender": "...",
    "subject": "...",
    "summary": "...",
    "needs_action": true,
    "urgency_score": 3,
    "priority_reason": "...",
    "dates_mentioned": "..."
  }}
]

Emails:
{emails_text}
"""

def call_llm(prompt: str) -> str:
    """Sends the prompt to the local Ollama model. Raises LLMError on
    any failure to reach or get a response from the model."""
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        raise LLMError(f"Failed to get a response from local LLM '{LLM_MODEL}': {e}") from e

def parse_response(raw_text: str) -> list[dict]:
    """Cleans and parses the LLM's response into structured data.
    Raises LLMError if the result isn't valid JSON, rather than
    passing broken data further down the pipeline."""
    cleaned = strip_json_fences(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(
            f"LLM did not return valid JSON. Raw output was: {raw_text[:300]}"
        ) from e

def summarize_emails(emails: list[dict]) -> list[dict]:
    """Full summarization pipeline: builds the prompt, calls the local
    LLM, parses and validates the result. Raises LLMError on any
    failure, with a specific message describing what went wrong."""

    if not emails:
        logger.info("No emails to summarize")
        return []

    logger.info(f"Summarizing {len(emails)} emails using model '{LLM_MODEL}'")

    prompt = build_prompt(emails)
    raw_response = call_llm(prompt)
    digest_items = parse_response(raw_response)

    logger.info(f"Summarization complete — {len(digest_items)} digest items produced")
    return digest_items