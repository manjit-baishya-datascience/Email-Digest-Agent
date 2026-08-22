# Project Notes — Professional Engineering Workflow

## 1. Requirements Clarification (before writing any code)

Before touching a keyboard, a professional would:

- **Re-read the spec and list every explicit requirement and every ambiguity** — e.g., "Option 1, 2, or 3? Which auth method? What counts as 'done'?"
- **If this were a real work project** (not a take-home), they'd ask a stakeholder clarifying questions rather than guess. Since this is a take-home with no one to ask, the professional move is to write down your assumptions explicitly in the README ("I chose Outlook + automated TOTP because X").

## 2. Design Before Code — A Lightweight Design Doc

Before implementation starts on anything nontrivial, engineers write a short design doc (even 1 page) covering:

- **Problem statement** — what are we building and why
- **Architecture diagram** — boxes and arrows: Camoufox → LangGraph nodes → LLM → disk output → FastAPI trigger
- **State schema** — exactly what data flows between components (e.g., `AgentState`)
- **Failure modes** — what can go wrong at each step, and what happens when it does (login fails, LLM returns bad JSON, network drops mid-scrape)
- **Alternatives considered** — e.g., "considered scraping via IMAP instead of browser automation, rejected because the assignment specifically requires browser automation"

This step feels slow but it's what separates "code that works once on my machine" from "code a team can trust and maintain."

## 3. Build in Isolated, Independently-Testable Increments

- **De-risk the riskiest/most uncertain piece first** (Camoufox launches, persists session) — professionals call this "de-risking" the project early
- **Then the next piece** (login flow), tested alone
- **Then scraping**, tested alone
- **Then LLM calls**, tested alone
- **Only then wire pieces together**

The professional reason for this order: if you wire everything together first and something breaks, you don't know which of five components failed. Isolated testing first means each piece has already proven itself before integration — so integration bugs are almost always about the wiring, not the components.

## 4. Version Control Discipline

A professional would, from commit #1:

- **Use small, frequent commits** with descriptive messages (not one giant commit at the end)
- **Never commit secrets** — `.gitignore` set up before the first commit, not after
- **Possibly work in a feature branch per component** (`git checkout -b scrape-node`) and merge into `main` once tested, especially on a team — though for a solo take-home, direct commits to `main` are completely normal

## 5. Testing Strategy

At a professional level, this project would have:

- **Unit tests** for pure logic (e.g., the JSON-fence-stripping function, the Markdown formatting function) — these don't need a browser or LLM running, so they're fast and run constantly
- **Integration tests** for the full pipeline, run less often since they're slow (real browser, real LLM)
- **A mocked/fixture-based test** — e.g., save one real scraped JSON file as a fixture, and test `summarize_node` + `save_node` against it without needing to re-scrape every time (this also protects against Outlook UI changes breaking unrelated tests)

For a take-home specifically, given the time budget, professionals would likely skip full test coverage and instead demonstrate testing awareness — e.g., one or two tests showing you know how, rather than exhaustive coverage. Over-investing in tests for a 3-5hr take-home would itself be a bad signal (poor time judgment).

## 6. Error Handling & Observability

Professional code doesn't just "handle errors" — it logs them usefully. Instead of `print()`, a real system would use Python's `logging` module with levels (`INFO`, `WARNING`, `ERROR`), so when something fails in production, you can trace what happened and when from log files, not guesswork.

## 7. Configuration Management

Professionals never hardcode values that might change — model names, timeouts, URLs, retry counts — these go into a config file or environment variables (already used via `.env` for secrets). Extending that same instinct to non-secret config (e.g., which Ollama model to use) is a nice touch.

## 8. Code Review (Even Solo)

At a company, no code ships without another engineer reviewing the pull request first — catching bugs, questioning design choices, enforcing consistency. Solo, you don't have that luxury, but the professional substitute is: **re-read your own code the next day with fresh eyes**, or literally explain each function out loud to yourself ("rubber duck" review) before considering it done.

## 9. Documentation as a First-Class Deliverable

A README isn't an afterthought — professionals write it thinking "a new engineer with zero context should be able to run this in under 10 minutes." That means:

- Exact setup commands
- Expected `.env` variables (names only, never real values)
- How to run it
- What success looks like
- Known limitations (e.g., "message previews are truncated by Outlook's UI, so long-body content extraction requires clicking into individual emails — noted as a future improvement")

## 10. Demo / Handoff

At many companies, before something ships, there's often a demo to the team — showing it work end-to-end, live, plus a fallback recording in case live demos fail (systems are flaky). This maps directly to a required screen recording — professionals over-prepare for demos because live failures are common and embarrassing.
