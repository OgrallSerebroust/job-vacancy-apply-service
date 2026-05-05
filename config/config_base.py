from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="settings/.env",
        env_file_encoding="UTF-8",
        extra="ignore"
    )
