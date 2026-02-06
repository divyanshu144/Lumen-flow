from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_name: str = "clientops-ai"

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    llm_provider: str = "openai"
    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60

settings = Settings()
