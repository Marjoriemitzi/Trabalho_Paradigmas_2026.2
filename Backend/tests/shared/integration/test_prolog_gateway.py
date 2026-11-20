from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from app.shared.infrastructure.prolog.gateway import PrologGateway

REGRAS = """
cor(azul).
cor(verde).
admin(root).
maior(X, Y) :- X > Y.
inteiro(X) :- integer(X).
dobro(X, Y) :- Y is X * 2.
"""

MAIOR_INTEIRO = 2**63 - 1
MENOR_INTEIRO = -(2**63)


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


def test_holds_compara_inteiros(prolog: PrologGateway) -> None:
    assert prolog.holds("maior", 30001, 30000) is True
    assert prolog.holds("maior", 30000, 30000) is False


def test_inteiro_chega_ao_prolog_como_inteiro(prolog: PrologGateway) -> None:
    assert prolog.holds("inteiro", 80000) is True


def test_numero_em_texto_continua_sendo_atomo(prolog: PrologGateway) -> None:
    assert prolog.holds("inteiro", "80000") is False


def test_values_calcula_com_inteiros(prolog: PrologGateway) -> None:
    resposta = prolog.values("dobro", 4_000_000_000_000_000_000)

    assert resposta == ["8000000000000000000"]


def test_aceita_inteiros_negativos(prolog: PrologGateway) -> None:
    assert prolog.holds("maior", -5, -10) is True


def test_aceita_os_limites_de_64_bits(prolog: PrologGateway) -> None:
    assert prolog.holds("maior", MAIOR_INTEIRO, MAIOR_INTEIRO - 1) is True
    assert prolog.holds("maior", MENOR_INTEIRO + 1, MENOR_INTEIRO) is True


@pytest.mark.parametrize("valor", [MAIOR_INTEIRO + 1, MENOR_INTEIRO - 1])
def test_recusa_inteiro_fora_de_64_bits(prolog: PrologGateway, valor: int) -> None:
    with pytest.raises(ValueError, match="64 bits"):
        prolog.holds("inteiro", valor)
    with pytest.raises(ValueError, match="64 bits"):
        prolog.values("dobro", valor)


@pytest.mark.parametrize("valor", [True, False, 1.5, None, b"azul"])
def test_recusa_argumento_que_nao_e_texto_nem_inteiro(
    prolog: PrologGateway, valor: Any
) -> None:
    with pytest.raises(TypeError):
        prolog.holds("inteiro", valor)
    with pytest.raises(TypeError):
        prolog.values("dobro", valor)
