import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env file from project root
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class Config:
    # Kommo Configuration
    KOMMO_SUBDOMAIN = os.getenv("KOMMO_SUBDOMAIN", "zelletotaltv")
    KOMMO_ACCESS_TOKEN = os.getenv("KOMMO_ACCESS_TOKEN", "")
    
    # Chatwoot Configuration
    CHATWOOT_BASE_URL = os.getenv("CHATWOOT_BASE_URL", "http://localhost:3000").rstrip("/")
    CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "1")
    CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN", "")
    CHATWOOT_INBOX_ID = os.getenv("CHATWOOT_INBOX_ID", "1")
    
    # Reporting & Idempotency Paths
    LOCAL_REPORT_PATH = os.getenv("LOCAL_REPORT_PATH", str(BASE_DIR / "output" / "migration_log.xlsx"))
    STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", str(BASE_DIR / "output" / "migration_state.json"))
    STAGE_OVERRIDES_PATH = os.getenv("STAGE_OVERRIDES_PATH", str(BASE_DIR / "stage_name_overrides.json"))

    @classmethod
    def validate_kommo(cls):
        if not cls.KOMMO_SUBDOMAIN or not cls.KOMMO_ACCESS_TOKEN:
            raise ValueError("Missing KOMMO_SUBDOMAIN or KOMMO_ACCESS_TOKEN in environment / .env file.")

    @classmethod
    def validate_chatwoot(cls, dry_run=False):
        if not dry_run:
            if not cls.CHATWOOT_BASE_URL or not cls.CHATWOOT_API_TOKEN or not cls.CHATWOOT_ACCOUNT_ID:
                raise ValueError("Missing CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID, or CHATWOOT_API_TOKEN in environment / .env file.")
