import ollama
import json
import os
from datetime import datetime

def summarize_emails(emails):
    email_text = "\n\n".join(
        f"Email {e['index']}: {e['raw_label']}" for e in emails
    )

    prompt = f"""You are an email assistant. Below are raw email previews scraped from an inbox.
Each entry may include sender, subject, time, and a preview snippet (sometimes truncated).

For each email, extract:
- sender
- subject
- a one-line summary
- whether it needs action (true/false)
- any specific dates mentioned (if none, say "none")

Only use information present in the text. Do not guess or invent details that aren't there.
If a snippet is cut off and you cannot determine something, say "unknown" rather than guessing.

Respond ONLY with valid JSON, in this exact format, and nothing else — no preamble, no markdown fences:
[
  {{
    "sender": "...",
    "subject": "...",
    "summary": "...",
    "needs_action": true,
    "dates_mentioned": "..."
  }}
]

Emails:
{email_text}
"""

    response = ollama.chat(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]


def parse_llm_json(raw_text):
    # Ollama sometimes wraps JSON in ```json fences despite instructions — strip if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned)


def save_markdown_digest(digest_items, filepath):
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

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    with open("scraped_data/inbox.json", "r", encoding="utf-8") as f:
        emails = json.load(f)

    raw_result = summarize_emails(emails)

    try:
        digest_items = parse_llm_json(raw_result)
    except json.JSONDecodeError:
        print("LLM did not return valid JSON. Raw output was:")
        print(raw_result)
        exit(1)

    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = f"outputs/digest_{timestamp}.md"

    save_markdown_digest(digest_items, md_path)
    print(f"Digest saved to {md_path}")