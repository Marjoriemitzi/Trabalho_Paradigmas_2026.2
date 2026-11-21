import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "src" / "app"
CONTEXTOS = ("users", "finance", "shared")
FRAMEWORKS = (
    "fastapi",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "pyswip",
    "jwt",
    "argon2",
)


def imports_de(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(apelido.name for apelido in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module)
    return nomes


def violacoes(pasta: str, proibidos: tuple[str, ...], *, raiz: Path = APP) -> list[str]:
    encontradas = []
    for arquivo in sorted((raiz / pasta).rglob("*.py")):
        for nome in sorted(imports_de(arquivo)):
            if any(nome == p or nome.startswith(f"{p}.") for p in proibidos):
                encontradas.append(f"{arquivo.relative_to(raiz)} importa {nome}")
    return encontradas


@pytest.mark.parametrize("contexto", CONTEXTOS)
def test_o_dominio_nao_depende_de_nenhuma_outra_camada(contexto: str) -> None:
    proibidos = (
        f"app.{contexto}.application",
        f"app.{contexto}.infrastructure",
        f"app.{contexto}.presentation",
        *FRAMEWORKS,
    )
    assert violacoes(f"{contexto}/domain", proibidos) == []


@pytest.mark.parametrize("contexto", CONTEXTOS)
def test_a_aplicacao_so_depende_do_dominio(contexto: str) -> None:
    proibidos = (
        f"app.{contexto}.infrastructure",
        f"app.{contexto}.presentation",
        *FRAMEWORKS,
    )
    assert violacoes(f"{contexto}/application", proibidos) == []


@pytest.mark.parametrize("contexto", CONTEXTOS)
def test_infraestrutura_e_apresentacao_nao_se_conhecem(contexto: str) -> None:
    assert (
        violacoes(f"{contexto}/infrastructure", (f"app.{contexto}.presentation",)) == []
    )
    assert (
        violacoes(f"{contexto}/presentation", (f"app.{contexto}.infrastructure",)) == []
    )


def test_o_finance_so_usa_a_autenticacao_do_users() -> None:
    permitido = "app.users.presentation.api.v1.security"
    usos = violacoes("finance", ("app.users",))
    assert [uso for uso in usos if not uso.endswith(f"importa {permitido}")] == []


def test_o_users_nao_conhece_o_finance() -> None:
    assert violacoes("users", ("app.finance",)) == []


def test_o_shared_nao_conhece_users_nem_finance() -> None:
    assert violacoes("shared", ("app.users", "app.finance")) == []


@pytest.mark.parametrize("contexto", ["users", "finance"])
def test_o_dominio_nao_depende_de_shared_infra_ou_apresentacao(contexto: str) -> None:
    proibidos = ("app.shared.infrastructure", "app.shared.presentation")
    assert violacoes(f"{contexto}/domain", proibidos) == []


def test_guarda_detecta_shared_importando_users_ou_finance(tmp_path: Path) -> None:
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    (shared_dir / "ruim.py").write_text(
        "import app.users.domain.entities.user\n"
        "from app.finance.domain.entities.account import Account\n",
        encoding="utf-8",
    )

    encontradas = violacoes("shared", ("app.users", "app.finance"), raiz=tmp_path)

    assert encontradas == [
        "shared/ruim.py importa app.finance.domain.entities.account",
        "shared/ruim.py importa app.users.domain.entities.user",
    ]


def test_guarda_detecta_dominio_importando_shared_infra_ou_apresentacao(
    tmp_path: Path,
) -> None:
    dominio = tmp_path / "finance" / "domain"
    dominio.mkdir(parents=True)
    (dominio / "ok.py").write_text(
        "from app.shared.domain.clock import Clock\n", encoding="utf-8"
    )
    (dominio / "ruim.py").write_text(
        "from app.shared.infrastructure.prolog.gateway import PrologGateway\n"
        "from app.shared.presentation.api.errors import ApiError\n",
        encoding="utf-8",
    )

    encontradas = violacoes(
        "finance/domain",
        ("app.shared.infrastructure", "app.shared.presentation"),
        raiz=tmp_path,
    )

    assert encontradas == [
        "finance/domain/ruim.py importa app.shared.infrastructure.prolog.gateway",
        "finance/domain/ruim.py importa app.shared.presentation.api.errors",
    ]
