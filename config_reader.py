from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    db_url: PostgresDsn

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
