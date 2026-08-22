import json
import logging
import ollama
from app.config import LLM_MODEL
from app.exceptions import LLMError
from app.utils import strip_json_fences

logger = logging.getLogger(__name__)


def build_prompt(email: dict) -> str:
    """Constructs the summarization prompt for a single email. Only the
    body (plus forwarded status, for context) is sent — sender, subject,
    message_id, and date are already known from scraping and are
    re-attached to the LLM's output afterward rather than being
    re-extracted by the model. Pure function — no LLM call, no side
    effects — easy to unit test independently of Ollama.

    One email per call, rather than a batch, because Ollama's JSON
    mode reliably produces a single well-formed object but is
    unreliable at producing a list of N objects matching N inputs —
    observed directly: batches of 15 truncated to 5 results, and
    batches of 5 collapsed into a single merged object."""

    return f"""You are an email assistant. Below is a single email body scraped from an inbox.
Note: if this is a forwarded copy (see Forwarded status below), the body already reflects the
ORIGINAL message content. Judge urgency based only on the email body's content, not on how or
when it was delivered, since forwarded emails here were manually forwarded by the same person.

Extract and return:
- summary: a one-line summary of the email
- needs_action: true or false, whether a response or action is required
- urgency_score: an integer from 1 (no urgency) to 5 (highly urgent), based only on content
- priority_reason: a short phrase explaining the urgency_score
- dates_mentioned: any specific dates mentioned in the body, or "none" if there are none

Only use information present in the text. Do not guess or invent details that are not there.
If something is unclear or missing, say "unknown" rather than guessing.

Respond ONLY with a single valid JSON object, in this exact format:
{{
  "summary": "...",
  "needs_action": true,
  "urgency_score": 3,
  "priority_reason": "...",
  "dates_mentioned": "..."
}}

Forwarded: {email['is_forwarded']}
Body: {email['body']}
"""


def call_llm(prompt: str) -> str:
    """Sends the prompt to the local Ollama model. Raises LLMError on
    any failure to reach or get a response from the model."""
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json"  # forces syntactically valid JSON output from Ollama
        )
        return response["message"]["content"]
    except Exception as e:
        raise LLMError(f"Failed to get a response from local LLM '{LLM_MODEL}': {e}") from e


def parse_response(raw_text: str) -> dict:
    """Cleans and parses the LLM's response into a single structured
    object. Raises LLMError if the result isn't valid JSON or isn't a
    JSON object, rather than passing broken data further down the
    pipeline."""
    cleaned = strip_json_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(
            f"LLM did not return valid JSON. Raw output was: {raw_text[:300]}"
        ) from e

    if not isinstance(parsed, dict):
        raise LLMError(
            f"Expected a JSON object but got {type(parsed).__name__}. "
            f"Raw output was: {raw_text[:300]}"
        )

    return parsed


def merge_with_scraped_data(email: dict, result: dict) -> dict:
    """Re-attaches the fields we already know from scraping (message_id,
    sender, subject, date_time) to the LLM's reasoning output (summary,
    urgency_score, etc.)."""
    return {
        "message_id": email["message_id"],
        "sender": email["sender_name"],
        "sender_email": email["sender_email"],
        "subject": email["subject"],
        "date_time": email["date_time"],
        "summary": result.get("summary", "unknown"),
        "needs_action": result.get("needs_action", False),
        "urgency_score": result.get("urgency_score", 1),
        "priority_reason": result.get("priority_reason", "unknown"),
        "dates_mentioned": result.get("dates_mentioned", "none"),
    }


def summarize_one(email: dict) -> dict:
    """Summarizes a single email: builds the prompt, calls the local
    LLM, parses the result, and merges it with the already-known
    scraped fields. Raises LLMError on any failure, with a specific
    message describing what went wrong."""
    prompt = build_prompt(email)
    raw_response = call_llm(prompt)
    result = parse_response(raw_response)
    return merge_with_scraped_data(email, result)


def summarize_emails(emails: list[dict]) -> list[dict]:
    """Full summarization pipeline. Each email is summarized with its
    own LLM call rather than batching multiple emails per call, since
    the local model reliably produces one well-formed JSON object but
    is unreliable at producing a correctly-sized list of objects.
    A single email's failure is logged and skipped rather than
    aborting the whole run, so one bad email does not lose the rest
    of the digest."""

    if not emails:
        logger.info("No emails to summarize")
        return []

    logger.info(f"Summarizing {len(emails)} emails individually using model '{LLM_MODEL}'")

    digest_items = []
    for i, email in enumerate(emails):
        try:
            digest_items.append(summarize_one(email))
        except LLMError as e:
            logger.warning(f"Skipping email {i + 1} ({email.get('subject')}) — {e}")

    logger.info(f"Summarization complete — {len(digest_items)} of {len(emails)} emails summarized")
    return digest_items