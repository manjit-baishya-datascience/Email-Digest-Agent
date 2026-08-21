import ollama
import json

def summarize_emails(emails):
    # Combine all emails into one block of text for the LLM
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

Respond ONLY with valid JSON, in this exact format:
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


if __name__ == "__main__":
    # Load your most recent scraped file — adjust filename as needed
    with open("scraped_data/inbox.json", "r", encoding="utf-8") as f:
        emails = json.load(f)

    result = summarize_emails(emails)
    print(result)