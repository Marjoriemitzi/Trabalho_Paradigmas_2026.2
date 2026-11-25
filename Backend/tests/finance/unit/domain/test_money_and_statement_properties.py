import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.finance.domain.entities.account import Account
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import MAX_CENTS, Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.statement import Statement
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.domain.value_objects.transfer_flows import TransferFlows
from tests.finance.fakes.fake_account_repository import FakeAccountRepository
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository
from tests.finance.fakes.fake_transfer_repository import FakeTransferRepository

pytestmark = pytest.mark.property

DONO = OwnerId(uuid.uuid4())
CONTA_PRINCIPAL = Account.open(DONO, AccountName("Corrente"), AccountKind.CHECKING)
CONTA_POUPANCA = Account.open(DONO, AccountName("Reserva"), AccountKind.WALLET)
CONTA_CARTAO = Account.open(DONO, AccountName("Cartão"), AccountKind.CREDIT_CARD)
CONTAS_AUXILIARES = (CONTA_POUPANCA.id, CONTA_CARTAO.id)

CENTS_MAX = MAX_CENTS
OPENING_MIN = -(2**60)
OPENING_MAX = 2**60

CENTS_ST = st.integers(min_value=1, max_value=CENTS_MAX)
OPENING_ST = st.integers(min_value=OPENING_MIN, max_value=OPENING_MAX)


@st.composite
def _periodos(draw: st.DrawFn) -> Period:
    inicio = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2098, 12, 31)))
    dias_extras = draw(st.integers(min_value=0, max_value=365))
    return Period(inicio, inicio + timedelta(days=dias_extras))


def _data_no_periodo(draw: st.DrawFn, periodo: Period) -> date:
    amplitude = (periodo.end - periodo.start).days
    deslocamento = draw(st.integers(min_value=0, max_value=amplitude))
    return periodo.start + timedelta(days=deslocamento)


def _transacao_no_periodo(
    draw: st.DrawFn, periodo: Period, conta: AccountId
) -> Transaction:
    kind = draw(st.sampled_from((TransactionKind.INCOME, TransactionKind.EXPENSE)))
    cents = draw(CENTS_ST)
    dia = _data_no_periodo(draw, periodo)
    return Transaction.record(
        owner=DONO,
        account=conta,
        kind=kind,
        amount=Money(cents),
        description=Description("Lançamento"),
        category=Category("outros"),
        occurred_on=dia,
    )


def _transferencia_no_periodo(
    draw: st.DrawFn, periodo: Period, conta: AccountId
) -> Transfer:
    outra = draw(st.sampled_from(CONTAS_AUXILIARES))
    entrada = draw(st.booleans())
    origem, destino = (outra, conta) if entrada else (conta, outra)
    cents = draw(CENTS_ST)
    dia = _data_no_periodo(draw, periodo)
    return Transfer.record(
        owner=DONO,
        source=origem,
        destination=destino,
        amount=Money(cents),
        description=Description("Transferência"),
        occurred_on=dia,
    )


@st.composite
def _cenario_extrato_geral(
    draw: st.DrawFn,
) -> tuple[Period, int, tuple[Transaction, ...]]:
    periodo = draw(_periodos())
    saldo_inicial = draw(OPENING_ST)
    quantidade = draw(st.integers(min_value=0, max_value=30))
    transacoes = tuple(
        _transacao_no_periodo(
            draw,
            periodo,
            draw(st.sampled_from((CONTA_PRINCIPAL.id, *CONTAS_AUXILIARES))),
        )
        for _ in range(quantidade)
    )
    return periodo, saldo_inicial, transacoes


@st.composite
def _cenario_extrato_por_conta(
    draw: st.DrawFn,
) -> tuple[Period, int, tuple[Transaction, ...], tuple[Transfer, ...]]:
    periodo = draw(_periodos())
    saldo_inicial = draw(OPENING_ST)
    qtd_tx = draw(st.integers(min_value=0, max_value=30))
    qtd_tr = draw(st.integers(min_value=0, max_value=30))
    transacoes = tuple(
        _transacao_no_periodo(draw, periodo, CONTA_PRINCIPAL.id) for _ in range(qtd_tx)
    )
    transferencias = tuple(
        _transferencia_no_periodo(draw, periodo, CONTA_PRINCIPAL.id)
        for _ in range(qtd_tr)
    )
    return periodo, saldo_inicial, transacoes, transferencias


@given(cenario=_cenario_extrato_geral())
def test_invariante_contabil_do_statement_geral(
    cenario: tuple[Period, int, tuple[Transaction, ...]],
) -> None:
    periodo, saldo_inicial, transacoes = cenario

    extrato = Statement(
        period=periodo,
        opening_balance_cents=saldo_inicial,
        transactions=transacoes,
    )

    delta_esperado = extrato.totals.income_cents - extrato.totals.expense_cents
    assert extrato.closing_balance_cents - saldo_inicial == delta_esperado
    assert extrato.transfer_flows == TransferFlows(incoming_cents=0, outgoing_cents=0)


@given(cenario=_cenario_extrato_por_conta())
def test_invariante_contabil_do_statement_com_transferencias(
    cenario: tuple[Period, int, tuple[Transaction, ...], tuple[Transfer, ...]],
) -> None:
    periodo, saldo_inicial, transacoes, transferencias = cenario

    extrato = Statement(
        period=periodo,
        opening_balance_cents=saldo_inicial,
        transactions=transacoes,
        transfers=transferencias,
        account=CONTA_PRINCIPAL.id,
    )

    delta_esperado = (
        extrato.totals.income_cents
        - extrato.totals.expense_cents
        + extrato.transfer_flows.incoming_cents
        - extrato.transfer_flows.outgoing_cents
    )
    assert extrato.closing_balance_cents - saldo_inicial == delta_esperado


@given(cenario=_cenario_extrato_por_conta(), data=st.data())
def test_comutatividade_e_aditividade_de_totals_transfers_e_statement(
    cenario: tuple[Period, int, tuple[Transaction, ...], tuple[Transfer, ...]],
    data: st.DataObject,
) -> None:
    periodo, saldo_inicial, transacoes, transferencias = cenario
    tx_permutadas = tuple(data.draw(st.permutations(list(transacoes))))
    tr_permutadas = tuple(data.draw(st.permutations(list(transferencias))))

    original = Statement(
        period=periodo,
        opening_balance_cents=saldo_inicial,
        transactions=transacoes,
        transfers=transferencias,
        account=CONTA_PRINCIPAL.id,
    )
    permutado = Statement(
        period=periodo,
        opening_balance_cents=saldo_inicial,
        transactions=tx_permutadas,
        transfers=tr_permutadas,
        account=CONTA_PRINCIPAL.id,
    )

    assert Totals.of(transacoes) == Totals.of(tx_permutadas)
    assert TransferFlows.of(transferencias, CONTA_PRINCIPAL.id) == TransferFlows.of(
        tr_permutadas, CONTA_PRINCIPAL.id
    )
    assert original.closing_balance_cents == permutado.closing_balance_cents

    corte_tx = len(transacoes) // 2
    tot_a = Totals.of(transacoes[:corte_tx])
    tot_b = Totals.of(transacoes[corte_tx:])
    assert original.totals == Totals(
        income_cents=tot_a.income_cents + tot_b.income_cents,
        expense_cents=tot_a.expense_cents + tot_b.expense_cents,
    )

    corte_tr = len(transferencias) // 2
    flx_a = TransferFlows.of(transferencias[:corte_tr], CONTA_PRINCIPAL.id)
    flx_b = TransferFlows.of(transferencias[corte_tr:], CONTA_PRINCIPAL.id)
    assert original.transfer_flows == TransferFlows(
        incoming_cents=flx_a.incoming_cents + flx_b.incoming_cents,
        outgoing_cents=flx_a.outgoing_cents + flx_b.outgoing_cents,
    )


@st.composite
def _uma_transacao(draw: st.DrawFn, periodo: Period, conta: AccountId) -> Transaction:
    return _transacao_no_periodo(draw, periodo, conta)


@st.composite
def _uma_transferencia(draw: st.DrawFn, periodo: Period, conta: AccountId) -> Transfer:
    return _transferencia_no_periodo(draw, periodo, conta)


@given(cenario=_cenario_extrato_por_conta(), data=st.data())
def test_simetria_de_criacao_e_remocao_nos_repositorios_fake(
    cenario: tuple[Period, int, tuple[Transaction, ...], tuple[Transfer, ...]],
    data: st.DataObject,
) -> None:
    periodo, saldo_inicial, transacoes, transferencias = cenario
    nova_tx = data.draw(_uma_transacao(periodo, CONTA_PRINCIPAL.id))
    nova_tr = data.draw(_uma_transferencia(periodo, CONTA_PRINCIPAL.id))

    async def verificar() -> None:
        contas_repo = FakeAccountRepository()
        tx_repo = FakeTransactionRepository()
        tr_repo = FakeTransferRepository()
        for conta in (CONTA_PRINCIPAL, CONTA_POUPANCA, CONTA_CARTAO):
            await contas_repo.add(conta)
        for tx in transacoes:
            await tx_repo.add(tx)
        for tr in transferencias:
            await tr_repo.add(tr)

        async def fechamento_atual() -> int:
            txs = await tx_repo.list_between(DONO, periodo, CONTA_PRINCIPAL.id)
            trs = await tr_repo.list_between(DONO, CONTA_PRINCIPAL.id, periodo)
            return Statement(
                period=periodo,
                opening_balance_cents=saldo_inicial,
                transactions=tuple(txs),
                transfers=tuple(trs),
                account=CONTA_PRINCIPAL.id,
            ).closing_balance_cents

        totais_antes = await tx_repo.totals_by_account(DONO)
        fluxos_antes = await tr_repo.flows_by_account(DONO)
        fechamento_antes = await fechamento_atual()

        await tx_repo.add(nova_tx)
        await tr_repo.add(nova_tr)
        await tx_repo.remove(nova_tx)
        await tr_repo.remove(nova_tr)

        assert await tx_repo.totals_by_account(DONO) == totais_antes
        assert await tr_repo.flows_by_account(DONO) == fluxos_antes
        assert await fechamento_atual() == fechamento_antes

    asyncio.run(verificar())


@given(cents=st.integers(min_value=1, max_value=MAX_CENTS))
def test_money_aceita_inteiros_positivos_ate_o_teto(cents: int) -> None:
    assert Money(cents).cents == cents


@given(cents=st.integers(max_value=0))
def test_money_rejeita_qualquer_inteiro_nao_positivo(cents: int) -> None:
    with pytest.raises(InvalidValueError) as erro:
        Money(cents)

    assert erro.value.problem == "not_positive"


@given(
    valor=st.one_of(
        st.booleans(),
        st.floats(allow_nan=True, allow_infinity=True),
        st.decimals(allow_nan=True, allow_infinity=True),
        st.text(),
        st.none(),
    )
)
def test_money_rejeita_qualquer_valor_nao_inteiro_em_runtime(
    valor: bool | float | Decimal | str | None,
) -> None:
    with pytest.raises(TypeError, match="inteiro"):
        Money(valor)  # type: ignore[arg-type]


@given(cents=st.integers(min_value=MAX_CENTS + 1))
def test_money_acima_do_teto_e_recusado_como_too_large(cents: int) -> None:
    with pytest.raises(InvalidValueError) as erro:
        Money(cents)
    assert erro.value.problem == "too_large"
