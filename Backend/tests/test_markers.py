import ast
import tomllib
from pathlib import Path

import pytest

from tests.conftest import SUITE_MARKERS, TESTS_DIR, markers_for_path

PYPROJECT = TESTS_DIR.parent / "pyproject.toml"
FIXTURES_DE_BANCO = frozenset(
    {
        "migrated_database",
        "connection",
        "session_factory",
        "session",
        "real_client",
        "fresh_email",
        "auth_headers",
        "carteira",
    }
)


def _parametros_de_teste(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.FunctionDef | ast.AsyncFunctionDef) and (
            no.name.startswith("test_")
        ):
            nomes.update(arg.arg for arg in no.args.args)
            nomes.update(arg.arg for arg in no.args.kwonlyargs)
    return nomes


@pytest.mark.parametrize(
    ("relativo", "esperados"),
    [
        ("finance/unit/domain/test_account.py", ("unit",)),
        (
            "finance/unit/fakes/test_fake_account_repository.py",
            ("unit", "contract"),
        ),
        ("shared/unit/test_clock.py", ("unit",)),
        ("finance/integration/test_prolog_categorizer.py", ("integration",)),
        (
            "finance/integration/test_sql_account_repository.py",
            ("integration", "contract"),
        ),
        ("finance/e2e/test_accounts_endpoint.py", ("e2e",)),
        ("finance/e2e/test_accounts_real.py", ("e2e", "real")),
        ("test_seed_demo_real.py", ("e2e", "real")),
        ("test_health.py", ("e2e",)),
        ("test_cors.py", ("e2e",)),
        ("test_architecture.py", ("unit",)),
        ("test_migrations.py", ("unit",)),
        ("test_rules.py", ("unit",)),
        ("test_api_codes.py", ("unit",)),
        ("test_openapi.py", ("unit",)),
        ("test_demo_plan.py", ("unit",)),
        ("desconhecido/test_orfao.py", ()),
    ],
)
def test_classificacao_por_caminho(relativo: str, esperados: tuple[str, ...]) -> None:
    assert markers_for_path(TESTS_DIR / relativo) == esperados


def test_contrato_de_adapter_recebe_marcador_contract() -> None:
    caminho = TESTS_DIR / "finance/integration/test_recurrence_rules.py"
    assert markers_for_path(caminho, is_contract=True) == ("integration", "contract")


def test_marcadores_do_conftest_batem_com_pyproject() -> None:
    dados = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    registrados = {
        linha.split(":", maxsplit=1)[0].strip()
        for linha in dados["tool"]["pytest"]["ini_options"]["markers"]
    }

    assert registrados == SUITE_MARKERS


def test_todo_arquivo_de_teste_recebe_ao_menos_um_marcador() -> None:
    orfaos = [
        str(arquivo.relative_to(TESTS_DIR))
        for arquivo in sorted(TESTS_DIR.rglob("test_*.py"))
        if not markers_for_path(arquivo)
    ]

    assert orfaos == []


def test_nenhum_teste_que_usa_postgres_entra_no_test_fast() -> None:
    vazamentos = []
    for arquivo in sorted(TESTS_DIR.rglob("test_*.py")):
        if not (_parametros_de_teste(arquivo) & FIXTURES_DE_BANCO):
            continue
        marcadores = set(markers_for_path(arquivo))
        if not (marcadores & {"integration", "real"}):
            vazamentos.append(str(arquivo.relative_to(TESTS_DIR)))

    assert vazamentos == []
