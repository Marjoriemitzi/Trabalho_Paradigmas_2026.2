from pathlib import Path
from typing import Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: SecretStr
    prolog_rules_dir: Path
    enable_docs: bool = False

    @classmethod
    def from_env(cls) -> Self:
        return cls()  # pyright: ignore[reportCallIssue]
