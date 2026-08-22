# **Design Document — Email Inbox Digest Agent**

## **1. Problem Statement**

Build an automated agent that logs into a webmail inbox, extracts recent messages, generates a structured summary of priority action items, and persists the result to disk — triggered on demand via an API endpoint. The agent must reuse an authenticated session across runs rather than logging in every time, and must avoid hallucinating information not present in the source emails.

## **2. Goals**

- Reuse an authenticated browser session across runs (no repeated login/2FA)
- Extract recent inbox messages using resilient, non-brittle selectors
- Summarize messages into a structured, hallucination-free digest
- Correctly surface priority/action-required items
- Persist the digest as a readable Markdown file
- Expose a simple trigger interface to run the pipeline on demand
- Handle failure at each stage gracefully rather than crashing

## **3. Architecture Overview**

```
FastAPI (POST /trigger)
        │
        ▼
LangGraph state machine
        │
        ├── scrape_inbox_node
        │     └── Camoufox (persistent session) → Outlook web inbox
        │           ├── list-view scrape (fast path, all messages)
        │           └── deep-read scrape (forwarded messages only)
        │
        ├── summarize_node
        │     └── Local LLM (Ollama) → structured JSON per email
        │
        └── save_node
              └── Markdown digest written to outputs/
```

Each node reads from and writes to a single shared state object. Conditional edges route to an error-handling node if any stage fails, rather than propagating an unhandled exception.

## **4. Component Details**

### **4.1 Browser & Session (Camoufox)**
- A persistent browser profile directory stores cookies/session tokens on disk, so a successful login is reused on all subsequent runs.
- Initial login is performed once, interactively, with 2FA (TOTP) completed manually; the resulting session is then reused headlessly.
- Dynamic waits (`wait_for_selector`) are used throughout instead of fixed sleeps, since the inbox UI loads asynchronously.

### **4.2 Scraping Strategy — Tiered Depth**
Two extraction paths, chosen per-message:

- **Shallow path (default):** every message's list-row `aria-label` attribute is read directly. This is fast and sufficient for native messages, where the full subject/sender/snippet is already present in that attribute.
- **Deep path (forwarded messages only):** messages detected as forwards (identified by the `"Forwarded message"` marker present in the row label) are opened individually so the full body text can be read from the reading pane. This is because forwarded content is frequently truncated in the list-row preview, hiding the actual detail (e.g., a specific date) that the summarization step needs.

This tiered approach was chosen over uniformly deep-scraping every message, to keep runtime reasonable on inboxes with many messages while still guaranteeing complete data on the subset where preview truncation would otherwise cause missing or inaccurate extraction.

### **4.3 Summarization (Local LLM via Ollama)**
- Each scraped message (shallow or deep) is passed to a locally running LLM with an instruction to extract: sender, subject, one-line summary, whether the message needs action, and any dates mentioned.
- The prompt explicitly instructs the model not to guess when information is not present, and to state "unknown" instead — prioritizing hallucination-free output over completeness.
- The prompt notes that some messages are self-forwarded copies, and instructs the model to judge priority from message content rather than delivery metadata, since every message in this inbox was manually curated and forwarded by the same person — removing the natural "who sent this and when" priority signal a real inbox would have.
- Output is required to be strict JSON; a lightweight cleanup step strips markdown code-fences if the model adds them despite instructions.

### **4.4 Persistence**
- The structured JSON digest is rendered into a human-readable Markdown file, with a dedicated "Needs Action" section surfaced above the full per-message listing.
- Output files are timestamped so repeated runs do not overwrite prior results.

### **4.5 Trigger Interface (FastAPI)**
- A single `POST /trigger` endpoint runs the full pipeline synchronously and returns the output path and summary metadata.
- Because the browser automation library used is synchronous and FastAPI runs an asyncio event loop, the pipeline is offloaded to a worker thread per request rather than run directly on the event loop.
- A `GET /health` endpoint is included for basic liveness checking.

## **5. State Schema**

| Field | Type | Description |
|---|---|---|
| `emails` | `Optional[List[dict]]` | Raw scraped message data (shallow and/or deep) |
| `digest_items` | `Optional[List[dict]]` | Structured LLM output per message |
| `output_path` | `Optional[str]` | Path to the saved Markdown digest |
| `error` | `Optional[str]` | Populated if any stage fails |

State fields are `Optional` because they are populated incrementally as the pipeline progresses; at the start of a run, none of them have values yet.

## **6. Failure Modes & Handling**

| Failure | Where it's caught | Behavior |
|---|---|---|
| Login/session expired or selector not found | `scrape_inbox_node` | Error captured in state, pipeline routes to error-handling node instead of crashing |
| Message list fails to load in time | `scrape_inbox_node` | Dynamic wait times out, caught and surfaced as an error rather than hanging indefinitely |
| LLM returns malformed/non-JSON output | `summarize_node` | Output is cleaned of markdown fences; if still unparseable, error is captured and reported rather than silently producing a broken digest |
| LLM lacks information to answer a field | `summarize_node` (prompt-level) | Model is instructed to respond "unknown" rather than guess |
| Disk write fails | `save_node` | Error captured in state |
| Sync browser automation invoked inside FastAPI's async event loop | API layer | Pipeline execution is offloaded to a separate thread |

## **7. Known Limitations**

- Priority ranking is based entirely on message content, since every message in the demo inbox was self-forwarded and therefore lacks the natural arrival-time/sender-relationship signals a live inbox would have.
- Forward detection relies on the literal `"Forwarded message"` marker Outlook inserts; a differently formatted forward (e.g., manually retyped rather than using the forward button) would not be caught by this rule.
- Session persistence depends on the stored browser profile remaining valid; an expired or revoked session would require one manual re-login.

## **8. Future Improvements**

- Extend the deep-read trigger beyond forwards to other heuristics (e.g., subject keywords, truncation detection).
- Add a fine-tuned local model specialized for the extraction task, in place of prompting a general-purpose model.
- Add retry logic for transient failures (e.g., a single retry on scrape timeout before routing to the error node).