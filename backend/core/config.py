from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Recruitment & Talent Management Copilot"
    api_prefix: str = "/api"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+aiomysql://hirepilot_user:hirepilot_password@localhost:3306/hirepilot_db",
    )
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    uploads_dir: str = os.getenv("UPLOADS_DIR", "uploads")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    def missing_smtp_settings(self) -> list[str]:
        missing: list[str] = []
        if not self.smtp_host:
            missing.append("SMTP_HOST")
        if not self.smtp_port:
            missing.append("SMTP_PORT")
        if not self.smtp_username:
            missing.append("SMTP_USERNAME")
        if not self.smtp_password:
            missing.append("SMTP_PASSWORD")
        if not self.smtp_from_email:
            missing.append("SMTP_FROM_EMAIL")
        return missing

    def validate_smtp_configuration(self) -> list[str]:
        issues = self.missing_smtp_settings()
        if self.smtp_host == "smtp.gmail.com":
            if self.smtp_port != 587:
                issues.append("SMTP_PORT must be 587 for Gmail SMTP")
            if not self.smtp_use_tls:
                issues.append("SMTP_USE_TLS must be enabled for Gmail SMTP")
        return issues


settings = Settings()




