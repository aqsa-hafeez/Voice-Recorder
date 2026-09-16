from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    elevenlabs_api_key: str
    audio_storage_dir: str = "/tmp/storage/audio"
    database_url: str = "sqlite:////tmp/storage/app.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
