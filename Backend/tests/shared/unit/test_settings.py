from pathlib import Path

import pytest
from pydantic import ValidationError

from app.shared.infrastructure.config.settings import Settings

URL = "postgresql+asyncpg://usuario:senha@db:5432/finance"


@pytest.fixture
def ambiente(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("PROLOG_RULES_DIR", "/app/rules")
    monkeypatch.delenv("ENABLE_DOCS", raising=False)
    return monkeypatch


def test_le_a_configuracao_do_ambiente(ambiente: pytest.MonkeyPatch) -> None:
    settings = Settings.from_env()

    assert settings.database_url.get_secret_value() == URL
    assert settings.prolog_rules_dir == Path("/app/rules")
    assert settings.enable_docs is False


def test_sem_url_do_banco_a_aplicacao_nao_sobe(ambiente: pytest.MonkeyPatch) -> None:
    ambiente.delenv("DATABASE_URL")
    with pytest.raises(ValidationError, match="database_url"):
        Settings.from_env()


def test_liga_a_documentacao_quando_pedido(ambiente: pytest.MonkeyPatch) -> None:
    ambiente.setenv("ENABLE_DOCS", "true")
    assert Settings.from_env().enable_docs is True


def test_a_url_do_banco_nao_aparece_em_logs(ambiente: pytest.MonkeyPatch) -> None:
    assert "senha" not in repr(Settings.from_env())
