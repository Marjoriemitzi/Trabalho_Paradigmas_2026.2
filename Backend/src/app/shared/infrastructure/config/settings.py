from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    database_url: SecretStr
    prolog_rules_dir: Path
    enable_docs: bool = False
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_expires_minutes: int = Field(default=30, gt=0)

    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = [x.strip() for x in v.split(",") if x.strip()]
        if isinstance(v, list):
            for origin in v:
                if origin == "*":
                    raise ValueError(
                        'CORS "*" não é permitido. Especifique as origens.'
                    )
                if not origin.startswith(("http://", "https://")):
                    raise ValueError(
                        f"Origem CORS deve ter esquema http/https: {origin}"
                    )
                if origin.endswith("/"):
                    raise ValueError(
                        f"Origem CORS não deve terminar com barra: {origin}"
                    )
        return v  # type: ignore
