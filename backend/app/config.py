from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./invoice_system.db"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AI_PROVIDER: str = "gemini"          # "gemini" | "openai"
    UPLOAD_DIR: str = "uploads"
    TOLERANCE_THRESHOLD: float = 0.02    # 2% tolerance — design assumption
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = ".env"


settings = Settings()
