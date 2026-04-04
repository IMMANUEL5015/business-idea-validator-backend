from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    ai_secret_key: str
    email_api_key: str
    jwt_secret_key: str
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()