import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    
    bot_token: str
    bitrix_webhook_url: str
    
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_db: str
    
    bitrix_source_id: str = "WEB"
    bitrix_assigned_by_id: int | None = None
    bitrix_lead_status_id: str = "NEW"

    @property
    def database_url(self) -> str:

        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

def load_settings() -> Settings:
    
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    bitrix_webhook_url = os.getenv("BITRIX_WEBHOOK_URL", "").strip().rstrip("/")
    bitrix_source_id = os.getenv("BITRIX_SOURCE_ID", "WEB").strip() or "WEB"
    bitrix_lead_status_id = os.getenv("BITRIX_LEAD_STATUS_ID", "NEW").strip() or "NEW"
    
    postgres_user = os.getenv("POSTGRES_USER", "").strip()
    postgres_password = os.getenv("POSTGRES_PASSWORD", "").strip()
    postgres_host = os.getenv("POSTGRES_HOST", "").strip()
    postgres_port = int(os.getenv("POSTGRES_PORT", "").strip())
    postgres_db = os.getenv("POSTGRES_DB", "").strip()

    assigned_by_raw = os.getenv("BITRIX_ASSIGNED_BY_ID")
    bitrix_assigned_by_id = int(assigned_by_raw) if assigned_by_raw else None

    if not bot_token:
        raise RuntimeError("BOT_TOKEN environment variable is required.")

    if not bitrix_webhook_url:
        raise RuntimeError("BITRIX_WEBHOOK_URL environment variable is required.")

    return Settings(
        bot_token=bot_token,
        bitrix_webhook_url=bitrix_webhook_url,
        bitrix_source_id=bitrix_source_id,
        bitrix_assigned_by_id=bitrix_assigned_by_id,
        bitrix_lead_status_id=bitrix_lead_status_id,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
    )


settings = load_settings()