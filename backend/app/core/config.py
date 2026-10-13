from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "mysql+pymysql://smart_inventory@localhost:3306/smart_inventory"
    cors_origins: list[str] = ["http://localhost:5173"]
    session_ttl_minutes: int = Field(default=480, ge=1, le=1440)
