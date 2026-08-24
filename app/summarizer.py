import json
import logging
import ollama
from app.config import LLM_MODEL, URGENCY_THRESHOLD
from app.exceptions import LLMError
from app.utils import strip_json_fences

logger = logging.getLogger(__name__)


def build_prompt(body: str) -> str:
    """Single prompt producing both summary and urgency_score together
    in one call — matches exactly what the fine-tuned model was
    trained on. Pure function — no LLM call, no side effects — easy
    to unit test independently of Ollama."""

    return f"""Read this email body and return a JSON object with:
- summary: a one-line summary of the email
- urgency_score: an integer from 1 to 5 rating how much timely action this email requires from the recipient:
  1 = no action needed (newsletters, receipts, FYI notices)
  2 = minor/optional action, no real deadline (casual invites, low-priority updates)
  3 = action expected but not time-critical (routine requests, non-urgent replies)
  4 = action needed soon (upcoming bill due, meeting confirmation, moderate deadline)
  5 = immediate action required (OTP/login codes, account security alerts, bills due imminently, someone actively waiting on a reply)

Base the score only on what's stated in the email. Do not guess or invent details that are not there.

Respond ONLY with a single valid JSON object, in this exact format:
{{"summary": "...", "urgency_score": 3}}

Body: {body}
"""


def build_overview_prompt(digest_items: list[dict]) -> str:
    """Builds a prompt that combines the ALREADY-GENERATED individual
    summaries into a single overall paragraph. Uses an explicit
    per-email delimiter so the model treats each summary as a
    distinct, separate item rather than blending unrelated emails
    together (e.g. a Microsoft sign-in alert and a Google sign-in
    alert must not be merged into one conflated statement)."""

    summary_blocks = []
    for item in digest_items:
        block = (
            f"Subject: {item['subject']}\n"
            f"Summary: {item['summary']}"
        )
        summary_blocks.append(block)

    emails_text = "\n--- END EMAIL ---\n".join(summary_blocks)

    return f"""You are an email assistant. Below are the individual summaries of several URGENT
emails from an inbox, separated by "--- END EMAIL ---" markers. Each is a SEPARATE, DISTINCT
email — do not merge or conflate details from different emails, even if they look similar
(e.g. a Microsoft sign-in alert and a Google sign-in alert are two different events, from two
different senders, and must be described separately).

Write a short overall summary (2-4 sentences) covering all of these urgent emails together,
mentioning each one individually rather than generalizing across all of them.

Respond ONLY with a single valid JSON object, in this exact format:
{{"overview": "..."}}

--- END EMAIL ---
{emails_text}
--- END EMAIL ---
"""


def call_llm(model: str, prompt: str) -> str:
    """Sends a prompt to the given Ollama model. Raises LLMError on any
    failure to reach or get a response from the model."""
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
        return response["message"]["content"]
    except Exception as e:
        raise LLMError(f"Failed to get a response from local LLM '{model}': {e}") from e


def parse_response(raw_text: str) -> dict:
    """Cleans and parses an LLM response into a single structured
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


def summarize_one(email: dict) -> dict:
    """Runs the fine-tuned model on a single email's body and returns
    both its summary and urgency_score in one call. Raises LLMError
    on failure."""
    prompt = build_prompt(email["body"])
    raw_response = call_llm(LLM_MODEL, prompt)
    result = parse_response(raw_response)

    return {
        "message_id": email["message_id"],
        "sender": email["sender_name"],
        "sender_email": email["sender_email"],
        "subject": email["subject"],
        "date_time": email["date_time"],
        "summary": result.get("summary", "unknown"),
        "urgency_score": int(result.get("urgency_score", 1)),
    }


def get_digest_overview(digest_items: list[dict]) -> str:
    """Generates one combined overview paragraph from the individual
    summaries already present in digest_items. Returns a fallback
    message on failure rather than raising, since this is an addition
    to the digest, not a required field."""

    if not digest_items:
        return "No urgent emails to summarize."

    try:
        prompt = build_overview_prompt(digest_items)
        raw_response = call_llm(LLM_MODEL, prompt)
        result = parse_response(raw_response)
        return result.get("overview", "unknown")
    except LLMError as e:
        logger.warning(f"Digest overview generation failed: {e}")
        return "Overview unavailable for this run."


def summarize_emails(emails: list[dict]) -> dict:
    """Full pipeline: runs the fine-tuned model once per email to get
    both summary and urgency_score, keeps only those meeting
    URGENCY_THRESHOLD, then produces one combined overview paragraph
    across the filtered set. A single email's failure is logged and
    skipped rather than aborting the whole run, so one bad email does
    not lose the rest of the digest. Returns a dict with both the
    per-email digest items and the overview."""

    if not emails:
        logger.info("No emails to process")
        return {"digest_items": [], "overview": "No emails to process."}

    logger.info(f"Summarizing {len(emails)} emails using model '{LLM_MODEL}'")

    scored_emails = []
    for i, email in enumerate(emails):
        try:
            scored_emails.append(summarize_one(email))
        except LLMError as e:
            logger.warning(f"Skipping email {i + 1} ({email.get('subject')}) — {e}")

    digest_items = [e for e in scored_emails if e["urgency_score"] >= URGENCY_THRESHOLD]
    logger.info(
        f"{len(digest_items)} of {len(scored_emails)} emails meet the urgency "
        f"threshold ({URGENCY_THRESHOLD})"
    )

    digest_items.sort(key=lambda item: item["urgency_score"], reverse=True)

    overview = get_digest_overview(digest_items)

    logger.info(f"Summarization complete — {len(digest_items)} urgent emails, overview generated")
    return {"digest_items": digest_items, "overview": overview}