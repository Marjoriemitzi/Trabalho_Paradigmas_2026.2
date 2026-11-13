from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: SecretStr
    prolog_rules_dir: Path
    enable_docs: bool = False
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_expires_minutes: int = Field(default=30, gt=0)
