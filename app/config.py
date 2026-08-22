import os
from pathlib import Path

# Project root (folder containing this app/ directory)
BASE_DIR = Path(__file__).resolve().parent.parent

# Persistent browser session storage
USER_DATA_DIR = str(BASE_DIR / "outlook_profile")

# Where scraped raw data and generated digests are saved
SCRAPED_DATA_DIR = str(BASE_DIR / "scraped_data")
OUTPUTS_DIR = str(BASE_DIR / "outputs")

# Outlook inbox URL
OUTLOOK_INBOX_URL = "https://outlook.com"

# Ollama model used for summarization
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")

# Timeouts (milliseconds, matching Playwright's convention)
MESSAGE_LIST_TIMEOUT_MS = 15000