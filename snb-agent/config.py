"""SNB Mission Hunter — Configuration centralisée."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

_HERE = Path(__file__).parent
_PROFILES_PATH = _HERE / "profiles.json"
_PROFILES_EXAMPLE_PATH = _HERE / "profiles.example.json"


@dataclass
class Config:
    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_to: str = ""
    score_threshold: int = 70
    scan_interval_fast: int = 300
    scan_interval_slow: int = 1800
    log_level: str = "INFO"
    active_profile: str = "baptiste"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            email_to=os.getenv("EMAIL_TO", ""),
            score_threshold=int(os.getenv("SCORE_THRESHOLD", "70")),
            scan_interval_fast=int(os.getenv("SCAN_INTERVAL_FAST", "300")),
            scan_interval_slow=int(os.getenv("SCAN_INTERVAL_SLOW", "1800")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            active_profile=os.getenv("ACTIVE_PROFILE", "baptiste"),
        )

    def validate(self) -> List[str]:
        errors = []
        if not self.supabase_url:
            errors.append("SUPABASE_URL")
        if not self.supabase_service_key:
            errors.append("SUPABASE_SERVICE_KEY")
        if not self.anthropic_api_key:
            import logging
            logging.getLogger("snb.main").warning("ANTHROPIC_API_KEY manquante — propositions IA desactivees")
        return errors


# CDI penalty keywords — missions CDI get score penalty
CDI_KEYWORDS = [
    "cdi", "permanent", "full-time employee", "salaire annuel",
    "annual salary", "benefits package", "mutuelle", "conges payes",
    "paid vacation", "w-2", "embauche", "poste fixe", "temps plein",
    "lundi au vendredi", "35h", "39h",
]

def _load_profiles() -> Dict[str, dict]:
    """Charge les profils depuis profiles.json (gitignoré, contient PII).

    Fallback sur profiles.example.json (anonymisé, committé) pour tests/CI.
    Retourne {} si aucun des deux n'existe.
    """
    path = _PROFILES_PATH if _PROFILES_PATH.exists() else _PROFILES_EXAMPLE_PATH
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


PROFILES: Dict[str, dict] = _load_profiles()
