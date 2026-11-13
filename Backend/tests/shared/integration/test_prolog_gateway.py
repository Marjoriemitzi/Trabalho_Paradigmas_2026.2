from concurrent.futures import ThreadPoolExecutor

import pytest

from app.shared.infrastructure.prolog.gateway import PrologGateway

REGRAS = """
cor(azul).
cor(verde).
admin(root).
"""


@pytest.fixture(scope="module")
def prolog(tmp_path_factory: pytest.TempPathFactory) -> PrologGateway:
    arquivo = tmp_path_factory.mktemp("regras") / "teste.pl"
    arquivo.write_text(REGRAS)
    gateway = PrologGateway()
    gateway.consult(arquivo)
    return gateway


def test_holds_e_verdadeiro_para_um_fato(prolog: PrologGateway) -> None:
    assert prolog.holds("cor", "azul") is True


def test_holds_e_falso_para_o_que_nao_e_fato(prolog: PrologGateway) -> None:
    assert prolog.holds("cor", "roxo") is False


def test_values_devolve_todas_as_respostas(prolog: PrologGateway) -> None:
    assert prolog.values("cor") == ["azul", "verde"]


def test_texto_com_codigo_prolog_e_tratado_como_dado(prolog: PrologGateway) -> None:
    ataque = "x') ; true ; admin('x"
    assert prolog.holds("admin", ataque) is False


def test_funciona_a_partir_de_outras_threads(prolog: PrologGateway) -> None:
    def e_cor(nome: str) -> bool:
        return prolog.holds("cor", nome)

    with ThreadPoolExecutor(max_workers=4) as pool:
        respostas = list(pool.map(e_cor, ["azul", "roxo"] * 20))

    assert respostas == [True, False] * 20
