from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None

    AUTO_MODE: bool = True
    APPROVAL_MODE: bool = False
    DRY_RUN: bool = False

    SAFE_BUDGET_CAP_DAILY: float = 300.0
    SAFE_BUDGET_CAP_WEEKLY: float = 1500.0

    META_ACCESS_TOKEN: str | None = None
    META_AD_ACCOUNT_ID: str | None = None
    META_PIXEL_ID: str | None = None
    META_APP_ID: str | None = None
    META_APP_SECRET: str | None = None

    TIKTOK_ACCESS_TOKEN: str | None = None
    TIKTOK_ADVERTISER_ID: str | None = None
    TIKTOK_OPEN_ID: str | None = None
    TIKTOK_PIXEL_ID: str | None = None

    INSTAGRAM_BUSINESS_ACCOUNT_ID: str | None = None

    STORAGE_BUCKET: str = "media"

    # Local AI services (via SupercomputerReconnect mesh)
    LLM_API_URL: str = "http://localhost:18080/v1"
    LLM_API_KEY: str | None = "omnimoney"
    LLM_MODEL: str = "qwen3.5-122b"
    ASR_API_URL: str = "http://localhost:18082"
    TTS_API_URL: str = "http://localhost:18083"

    PROXY_SERVER: str | None = None
    PROXY_USERNAME: str | None = None
    PROXY_PASSWORD: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
