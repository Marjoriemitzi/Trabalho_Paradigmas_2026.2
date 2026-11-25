import runpy
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr

from app.export_openapi import main, render_openapi
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


@pytest.mark.parametrize("argv", [[], ["a.json", "b.json"]])
def test_main_sem_exatamente_um_destino_responde_2_com_o_uso(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(argv) == 2

    saida = capsys.readouterr()
    assert saida.err == "uso: python -m app.export_openapi <arquivo.json>\n"
    assert saida.out == ""


def test_main_grava_o_contrato_igual_ao_versionado(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destino = tmp_path / "out.json"

    assert main([str(destino)]) == 0

    assert destino.read_text(encoding="utf-8") == ARQUIVO.read_text(encoding="utf-8")
    assert capsys.readouterr().out == f"OpenAPI gravado em {destino}\n"


def test_rodar_como_modulo_sai_com_o_codigo_do_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destino = tmp_path / "modulo.json"
    monkeypatch.setattr(sys, "argv", ["export_openapi", str(destino)])

    # Tira o módulo já importado para o runpy executá-lo do zero, sem aviso.
    monkeypatch.delitem(sys.modules, "app.export_openapi", raising=False)
    with pytest.raises(SystemExit) as saida:
        runpy.run_module("app.export_openapi", run_name="__main__")

    assert saida.value.code == 0
    assert destino.read_text(encoding="utf-8") == ARQUIVO.read_text(encoding="utf-8")
