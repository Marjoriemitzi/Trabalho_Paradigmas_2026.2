import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "src" / "app"
CATALOGO = RAIZ / "docs" / "api-codes.md"
DERIVA_DO_STATUS = "error_handlers.py"
CHAMADAS_DE_ERRO = {"error_response", "ApiError"}
CHAMADAS_DE_AVISO = {"TransactionWarning"}


def _nome(chamada: ast.Call) -> str | None:
    funcao = chamada.func
    if isinstance(funcao, ast.Name):
        return funcao.id
    if isinstance(funcao, ast.Attribute):
        return funcao.attr
    return None


def _argumento_do_codigo(chamada: ast.Call, nome: str) -> ast.expr | None:
    posicao = 1 if nome in CHAMADAS_DE_ERRO else 0
    if len(chamada.args) > posicao:
        return chamada.args[posicao]
    return next((k.value for k in chamada.keywords if k.arg == "code"), None)


def codigos_no_codigo() -> tuple[set[str], list[str]]:
    literais: set[str] = set()
    nao_literais: list[str] = []
    for arquivo in sorted(APP.rglob("*.py")):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if not isinstance(no, ast.Call):
                continue
            nome = _nome(no)
            if nome not in CHAMADAS_DE_ERRO | CHAMADAS_DE_AVISO:
                continue
            argumento = _argumento_do_codigo(no, nome)
            if isinstance(argumento, ast.Constant) and isinstance(argumento.value, str):
                literais.add(argumento.value)
            elif argumento is not None and arquivo.name != DERIVA_DO_STATUS:
                local = f"{arquivo.relative_to(APP)}:{no.lineno}"
                nao_literais.append(f"{local} ({nome})")
    return literais, nao_literais


def codigos_do_catalogo() -> set[str]:
    linhas = CATALOGO.read_text(encoding="utf-8").splitlines()
    achados = (re.match(r"^\|\s*`([a-z_0-9]+)`\s*\|", linha) for linha in linhas)
    return {m.group(1) for m in achados if m is not None}


def test_todo_codigo_e_uma_string_literal() -> None:
    _, nao_literais = codigos_no_codigo()

    assert nao_literais == [], (
        "O código de erro ou de aviso precisa ser uma string literal: "
        + ", ".join(nao_literais)
    )


def test_todo_codigo_emitido_esta_no_catalogo() -> None:
    literais, _ = codigos_no_codigo()

    faltam = sorted(literais - codigos_do_catalogo())

    assert faltam == [], f"Faltam em Backend/docs/api-codes.md: {', '.join(faltam)}"


def test_o_catalogo_lista_os_codigos_derivados_do_status() -> None:
    catalogo = codigos_do_catalogo()

    assert {"not_found", "method_not_allowed"} <= catalogo
