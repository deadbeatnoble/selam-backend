from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./selammind.db"
    secret_key: str = "selammind-hackathon-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "selammind@localhost"
    smtp_use_tls: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
