from pathlib import Path
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    database_url: SecretStr
    prolog_rules_dir: Path
    enable_docs: bool = False
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_expires_minutes: int = Field(default=15, gt=0)
    refresh_token_days: int = Field(default=30, gt=0)
    login_pair_max_failures: int = Field(default=5, gt=0)
    login_ip_max_failures: int = Field(default=50, gt=0)
    login_window_minutes: int = Field(default=15, gt=0)
    register_ip_max: int = Field(default=5, gt=0)
    register_window_minutes: int = Field(default=60, gt=0)
    app_env: Literal["development", "test", "production"] = "production"
    timezone: str = "America/Sao_Paulo"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _separa_as_origens(cls, valor: object) -> object:
        if isinstance(valor, str):
            return [parte.strip() for parte in valor.split(",") if parte.strip()]
        return valor

    @field_validator("cors_origins")
    @classmethod
    def _confere_as_origens(cls, origens: list[str]) -> list[str]:
        for origem in origens:
            if origem == "*":
                raise ValueError('CORS "*" não é permitido: liste cada origem')
            if not origem.startswith(("http://", "https://")):
                raise ValueError(
                    f"A origem CORS precisa do esquema http/https: {origem}"
                )
            if origem.endswith("/"):
                raise ValueError(f"A origem CORS não pode terminar com barra: {origem}")
        return origens

    @field_validator("timezone")
    @classmethod
    def _confere_o_fuso(cls, nome: str) -> str:
        try:
            ZoneInfo(nome)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"Fuso horário desconhecido: {nome}") from error
        return nome
