from camoufox.sync_api import Camoufox
from config import USER_DATA_DIR
from state import AgentState
import ollama
import json
import os
from datetime import datetime


def scrape_inbox_node(state: AgentState) -> dict:
    try:
        with Camoufox(headless=True, persistent_context=True, user_data_dir=USER_DATA_DIR) as browser:
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://outlook.com")
            page.wait_for_selector('[role="complementary"][aria-label="Message list"]', timeout=15000)

            rows = page.locator('[role="option"]')
            count = rows.count()

            emails = []
            for i in range(count):
                label = rows.nth(i).get_attribute("aria-label")
                emails.append({"index": i + 1, "raw_label": label})

            return {"emails": emails}

    except Exception as e:
        return {"error": f"Scraping failed: {str(e)}"}


def summarize_node(state: AgentState) -> dict:
    if state.get("error"):
        return {}  # skip if a previous node already failed

    emails = state["emails"]
    email_text = "\n\n".join(f"Email {e['index']}: {e['raw_label']}" for e in emails)

    prompt = f"""You are an email assistant. Below are raw email previews scraped from an inbox.

For each email extract: sender, subject, a one-line summary, whether it needs action (true/false), and any dates mentioned (or "none").
Only use information present in the text — do not guess. If unclear, say "unknown".

Respond ONLY with valid JSON, no preamble, no markdown fences:
[
  {{"sender": "...", "subject": "...", "summary": "...", "needs_action": true, "dates_mentioned": "..."}}
]

Emails:
{email_text}
"""

    try:
        response = ollama.chat(model="llama3.1", messages=[{"role": "user", "content": prompt}])
        raw = response["message"]["content"].strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        digest_items = json.loads(raw)
        return {"digest_items": digest_items}

    except Exception as e:
        return {"error": f"Summarization failed: {str(e)}"}


def save_node(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    digest_items = state["digest_items"]
    lines = [f"# Inbox Digest — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]

    action_items = [item for item in digest_items if item.get("needs_action")]
    if action_items:
        lines.append("## ⚠️ Needs Action\n")
        for item in action_items:
            lines.append(f"- **{item['subject']}** (from {item['sender']}) — {item['summary']}")
        lines.append("")

    lines.append("## All Messages\n")
    for item in digest_items:
        lines.append(f"### {item['subject']}")
        lines.append(f"- **From:** {item['sender']}")
        lines.append(f"- **Summary:** {item['summary']}")
        lines.append(f"- **Needs action:** {item['needs_action']}")
        lines.append(f"- **Dates mentioned:** {item['dates_mentioned']}")
        lines.append("")

    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"outputs/digest_{timestamp}.md"

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {"output_path": path}


def error_node(state: AgentState) -> dict:
    print(f"PIPELINE FAILED: {state.get('error')}")
    return {}