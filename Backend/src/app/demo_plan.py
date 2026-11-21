"""O que o comando de dados de demonstração cria, calculado a partir de "hoje".

Só dados e datas: nada de banco, framework ou casos de uso. É determinístico.
"""

import calendar
from dataclasses import dataclass
from datetime import date

CARTEIRA, CORRENTE, CARTAO = "Carteira", "Conta corrente", "Cartão"
MESES_ANTERIORES = 3


@dataclass(frozen=True, slots=True)
class AccountPlan:
    name: str
    kind: str


@dataclass(frozen=True, slots=True)
class TransactionPlan:
    account: str
    kind: str
    amount_cents: int
    description: str
    occurred_on: date
    category: str | None = None


@dataclass(frozen=True, slots=True)
class TransferPlan:
    source: str
    destination: str
    amount_cents: int
    description: str
    occurred_on: date


@dataclass(frozen=True, slots=True)
class RecurrencePlan:
    account: str
    kind: str
    amount_cents: int
    description: str
    category: str | None
    frequency: str
    day: int
    starts_on: date


@dataclass(frozen=True, slots=True)
class DemoPlan:
    accounts: tuple[AccountPlan, ...]
    transactions: tuple[TransactionPlan, ...]
    transfers: tuple[TransferPlan, ...]
    recurrences: tuple[RecurrencePlan, ...]


def _primeiro_dia_do_mes(hoje: date, deslocamento: int) -> date:
    indice = hoje.year * 12 + (hoje.month - 1) + deslocamento
    return date(indice // 12, indice % 12 + 1, 1)


def _dia(mes: date, dia: int) -> date:
    ultimo = calendar.monthrange(mes.year, mes.month)[1]
    return date(mes.year, mes.month, min(dia, ultimo))


def build_plan(today: date) -> DemoPlan:
    transacoes: list[TransactionPlan] = []
    transferencias: list[TransferPlan] = []

    def receita(conta: str, centavos: int, texto: str, quando: date) -> None:
        transacoes.append(TransactionPlan(conta, "income", centavos, texto, quando))

    def despesa(
        conta: str, centavos: int, texto: str, quando: date, categoria: str | None
    ) -> None:
        transacoes.append(
            TransactionPlan(conta, "expense", centavos, texto, quando, categoria)
        )

    for deslocamento in range(-MESES_ANTERIORES, 1):
        mes = _primeiro_dia_do_mes(today, deslocamento)
        receita(CORRENTE, 520000, "Salário", _dia(mes, 5))
        despesa(CORRENTE, 150000, "Aluguel", _dia(mes, 5), None)
        for dia in (7, 14, 21, 28):
            despesa(CORRENTE, 23000, "Supermercado", _dia(mes, dia), None)
        despesa(CORRENTE, 4590, "Uber", _dia(mes, 9), None)
        despesa(CARTAO, 5590, "Netflix", _dia(mes, 12), "lazer")
        despesa(CARTAO, 12000, "Farmácia", _dia(mes, 18), None)
        despesa(CARTEIRA, 2390, "Lanche da tarde", _dia(mes, 22), "outros")
        transferencias.append(
            TransferPlan(CORRENTE, CARTEIRA, 20000, "Para a carteira", _dia(mes, 10))
        )
    receita(
        CORRENTE,
        85000,
        "Freelance de design",
        _dia(_primeiro_dia_do_mes(today, -2), 20),
    )

    return DemoPlan(
        accounts=(
            AccountPlan(CARTEIRA, "wallet"),
            AccountPlan(CORRENTE, "checking"),
            AccountPlan(CARTAO, "credit_card"),
        ),
        transactions=tuple(t for t in transacoes if t.occurred_on <= today),
        transfers=tuple(t for t in transferencias if t.occurred_on <= today),
        recurrences=(
            RecurrencePlan(
                CORRENTE, "expense", 9990, "Academia", "saude", "monthly", 10, today
            ),
            RecurrencePlan(
                CARTEIRA, "expense", 6000, "Feira", "mercado", "weekly", 6, today
            ),
        ),
    )
