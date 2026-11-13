from pathlib import Path

import pytest
from pydantic import ValidationError

from app.shared.infrastructure.config.settings import Settings

URL = "postgresql+asyncpg://usuario:senha@db:5432/finance"
SEGREDO = "a" * 32


@pytest.fixture
def ambiente(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("PROLOG_RULES_DIR", "/app/rules")
    monkeypatch.setenv("JWT_SECRET", SEGREDO)
    monkeypatch.delenv("JWT_EXPIRES_MINUTES", raising=False)
    monkeypatch.delenv("ENABLE_DOCS", raising=False)
    return monkeypatch


def test_le_a_configuracao_do_ambiente(ambiente: pytest.MonkeyPatch) -> None:
    settings = Settings()

    assert settings.database_url.get_secret_value() == URL
    assert settings.prolog_rules_dir == Path("/app/rules")
    assert settings.enable_docs is False


def test_sem_url_do_banco_a_aplicacao_nao_sobe(ambiente: pytest.MonkeyPatch) -> None:
    ambiente.delenv("DATABASE_URL")
    with pytest.raises(ValidationError, match="database_url"):
        Settings()


def test_liga_a_documentacao_quando_pedido(ambiente: pytest.MonkeyPatch) -> None:
    ambiente.setenv("ENABLE_DOCS", "true")
    assert Settings().enable_docs is True


def test_a_url_do_banco_nao_aparece_em_logs(ambiente: pytest.MonkeyPatch) -> None:
    assert "senha" not in repr(Settings())


def test_le_o_segredo_e_a_validade_do_token(ambiente: pytest.MonkeyPatch) -> None:
    settings = Settings()

    assert settings.jwt_secret.get_secret_value() == SEGREDO
    assert settings.jwt_expires_minutes == 30


def test_recusa_segredo_curto_demais(ambiente: pytest.MonkeyPatch) -> None:
    ambiente.setenv("JWT_SECRET", "a" * 31)
    with pytest.raises(ValidationError, match="jwt_secret"):
        Settings()


def test_o_segredo_do_token_nao_aparece_em_logs(ambiente: pytest.MonkeyPatch) -> None:
    assert SEGREDO not in repr(Settings())
