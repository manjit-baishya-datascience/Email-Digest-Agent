# Email Digest Agent

An autonomous browser agent that logs into a webmail inbox, extracts recent messages, rates urgency using a fine-tuned local LLM, summarizes urgent messages using a base local LLM, and saves a Markdown digest — orchestrated with LangGraph and triggered via FastAPI.

See [`docs/design.md`](docs/design.md) for architecture, design decisions, and known limitations.

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running
- A Microsoft/Outlook account (a dedicated test account is recommended, not your primary inbox)

---

## Setup

### 1. Clone and install

```cmd
git clone https://github.com/manjit-baishya-datascience/Email-Digest-Agent.git
cd email-digest-agent
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
camoufox fetch
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in:

```
OUTLOOK_EMAIL=your_test_account@outlook.com
OUTLOOK_PASSWORD=your_password
OUTLOOK_TOTP_SECRET=your_totp_secret          # only needed for scripts/auto_login.py
```

Never commit `.env` — it's already listed in `.gitignore`.

### 3. Pull the required local models

```cmd
ollama pull llama3.1
```

To use the fine-tuned urgency model, register the exported GGUF:

```cmd
cd finetune_data\gguf_export
ollama create email-urgency-model -f Modelfile
```

Then set in `app/config.py` (or via environment variable):

```
LLM_MODEL=email-urgency-model
SUMMARY_MODEL=llama3.1
```

### 4. Authenticate once

```cmd
python scripts\login_setup.py
```

A visible browser window opens. Log in manually (including 2FA) the first time; the session is saved to `outlook_profile/` and reused automatically on every future run.

(Optional) To fully automate this step including 2FA, use `scripts/auto_login.py` instead, once `OUTLOOK_TOTP_SECRET` is set in `.env`.

### 5. Run the agent

```cmd
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs`, expand `POST /trigger`, and execute it. The generated digest is saved to `outputs/` and its path is returned in the response.

`GET /health` is available for a basic liveness check.

---

## Testing

```cmd
pytest
```

Runs the unit test suite covering pure/side-effect-free logic. Scraping and LLM behavior are validated via `scripts/*_manual_test.py` and the demo recording — see `docs/design.md` for why.

---

## Fine-Tuning

The LoRA fine-tuning and evaluation notebook is at [`notebooks/LoRA_Finetuning.ipynb`](notebooks/LoRA_Finetuning.ipynb). See `docs/design.md` for the rationale and results.