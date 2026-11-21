from pathlib import Path

from pydantic import SecretStr

from app.export_openapi import render_openapi
from app.shared.infrastructure.config.settings import Settings

ARQUIVO = Path(__file__).resolve().parents[1] / "openapi" / "openapi.json"
COMANDO = "docker compose run --rm --no-deps tools task openapi"


def configuracao(*, enable_docs: bool = False) -> Settings:
    return Settings(
        database_url=SecretStr("postgresql+asyncpg://u:s@localhost/finance"),
        prolog_rules_dir=Path("rules"),
        jwt_secret=SecretStr("s" * 32),
        enable_docs=enable_docs,
    )


def test_o_arquivo_versionado_esta_em_dia_com_a_aplicacao() -> None:
    gerado = render_openapi(configuracao())

    assert (
        ARQUIVO.read_text(encoding="utf-8") == gerado
    ), f"O contrato mudou e o arquivo está desatualizado: rode `{COMANDO}`."


def test_o_esquema_e_o_mesmo_com_a_documentacao_ligada_ou_desligada() -> None:
    assert render_openapi(configuracao(enable_docs=False)) == render_openapi(
        configuracao(enable_docs=True)
    )


def test_gerar_duas_vezes_produz_o_mesmo_texto() -> None:
    assert render_openapi(configuracao()) == render_openapi(configuracao())
