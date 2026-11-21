import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.prolog.prolog_categorizer import PrologCategorizer
from app.shared.infrastructure.prolog.gateway import PrologGateway
from app.users.domain.exceptions import WeakPasswordError
from app.users.infrastructure.prolog.prolog_password_policy import (
    PrologPasswordPolicy,
)

RULES_DIR = Path(__file__).resolve().parents[3] / "rules"

REGRAS = """
cor(azul).
cor(verde).
admin(root).
maior(X, Y) :- X > Y.
inteiro(X) :- integer(X).
dobro(X, Y) :- Y is X * 2.
comprimento(S, L) :- string_length(S, L).
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
    prolog: PrologGateway,
    valor: Any,  # noqa: ANN401 - o teste passa de propósito tipos que a API recusa
) -> None:
    with pytest.raises(TypeError):
        prolog.holds("inteiro", valor)
    with pytest.raises(TypeError):
        prolog.values("dobro", valor)


@pytest.mark.parametrize("texto", ["\x00", "abc\x00def", "supermercado\x00"])
def test_recusa_texto_com_byte_nul(prolog: PrologGateway, texto: str) -> None:
    with pytest.raises(ValueError, match="NUL"):
        prolog.holds("cor", texto)
    with pytest.raises(ValueError, match="NUL"):
        prolog.values("dobro", texto)


@pytest.mark.parametrize(("texto", "tamanho"), [("🛒", 1), ("SÁLÁRIO", 7), ("A1🛒", 3)])
def test_preserva_tamanho_em_codepoints_utf8(
    prolog: PrologGateway, texto: str, tamanho: int
) -> None:
    assert prolog.values("comprimento", texto) == [str(tamanho)]


def _checar_senha(policy: PrologPasswordPolicy, senha: str) -> str:
    try:
        policy.check(senha)
    except WeakPasswordError as erro:
        return ",".join(sorted(erro.reasons))
    return "ok"


def _executar_caso_misto(
    prolog: PrologGateway,
    categorizer: PrologCategorizer,
    policy: PrologPasswordPolicy,
    indice: int,
) -> tuple[str, object]:
    ramo = indice % 6
    if ramo == 0:
        return (
            "cat_mercado",
            categorizer.categorize(
                TransactionKind.EXPENSE, Description(f"Supermercado #{indice}")
            ).name,
        )
    if ramo == 1:
        return (
            "cat_salario",
            categorizer.categorize(
                TransactionKind.INCOME, Description(f"Salário #{indice}")
            ).name,
        )
    if ramo == 2:
        return ("pw_forte", _checar_senha(policy, f"S3nha!Forte{indice}"))
    if ramo == 3:
        return ("pw_fraca", _checar_senha(policy, "abc"))
    if ramo == 4:
        return ("tmp_cor", prolog.holds("cor", "azul"))
    return ("tmp_dobro", prolog.values("dobro", indice))


def _esperado_caso_misto(indice: int) -> tuple[str, object]:
    ramo = indice % 6
    if ramo == 0:
        return ("cat_mercado", "mercado")
    if ramo == 1:
        return ("cat_salario", "salario")
    if ramo == 2:
        return ("pw_forte", "ok")
    if ramo == 3:
        return ("pw_fraca", "no_digit,no_symbol,no_upper,too_short")
    if ramo == 4:
        return ("tmp_cor", True)
    return ("tmp_dobro", [str(indice * 2)])


def test_concorrencia_mista_entre_regras_nao_troca_resultados(
    prolog: PrologGateway,
) -> None:
    categorizer = PrologCategorizer(prolog, RULES_DIR)
    policy = PrologPasswordPolicy(prolog, RULES_DIR)
    indices = list(range(72))

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(
            pool.map(
                lambda i: _executar_caso_misto(prolog, categorizer, policy, i),
                indices,
            )
        )

    assert resultados == [_esperado_caso_misto(i) for i in indices]


async def test_concorrencia_assincrona_mista_com_to_thread(
    prolog: PrologGateway,
) -> None:
    categorizer = PrologCategorizer(prolog, RULES_DIR)
    policy = PrologPasswordPolicy(prolog, RULES_DIR)
    indices = list(range(60))

    resultados = await asyncio.gather(
        *(
            asyncio.to_thread(_executar_caso_misto, prolog, categorizer, policy, i)
            for i in indices
        )
    )

    assert list(resultados) == [_esperado_caso_misto(i) for i in indices]
