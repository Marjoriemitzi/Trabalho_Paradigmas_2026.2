from datetime import date

import pytest

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_id import TransactionId
from app.finance.domain.value_objects.transaction_kind import TransactionKind

NOVEMBRO = Period(date(2026, 11, 1), date(2026, 11, 30))
RECEITA, DESPESA = TransactionKind.INCOME, TransactionKind.EXPENSE


def lancamento(
    dono: OwnerId,
    conta: AccountId,
    dia: date,
    kind: TransactionKind = DESPESA,
    cents: int = 1250,
) -> Transaction:
    categoria = Category("mercado" if kind is DESPESA else "salario")
    return Transaction.record(
        owner=dono,
        account=conta,
        kind=kind,
        amount=Money(cents),
        description=Description("Supermercado"),
        category=categoria,
        occurred_on=dia,
    )


class TransactionRepositoryContract:
    @pytest.fixture
    def repository(self) -> TransactionRepository:
        raise NotImplementedError

    @pytest.fixture
    def dono(self) -> OwnerId:
        raise NotImplementedError

    @pytest.fixture
    def outro_dono(self) -> OwnerId:
        raise NotImplementedError

    @pytest.fixture
    def conta(self, dono: OwnerId) -> AccountId:
        raise NotImplementedError

    @pytest.fixture
    def outra_conta(self, dono: OwnerId) -> AccountId:
        raise NotImplementedError

    @pytest.fixture
    def conta_do_outro(self, outro_dono: OwnerId) -> AccountId:
        raise NotImplementedError

    async def test_quem_nao_lancou_nada_tem_extrato_vazio(
        self, repository: TransactionRepository, dono: OwnerId
    ) -> None:
        assert await repository.list_between(dono, NOVEMBRO) == []

    async def test_traz_a_transacao_do_periodo_com_todos_os_dados(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        gravada = lancamento(dono, conta, date(2026, 11, 7))
        await repository.add(gravada)

        [lida] = await repository.list_between(dono, NOVEMBRO)

        assert lida.id == gravada.id
        assert lida.owner == gravada.owner
        assert lida.account == gravada.account
        assert lida.kind is gravada.kind
        assert lida.amount == gravada.amount
        assert lida.description == gravada.description
        assert lida.category == gravada.category
        assert lida.occurred_on == gravada.occurred_on

    async def test_o_primeiro_e_o_ultimo_dia_do_periodo_entram(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        for dia in (date(2026, 10, 31), date(2026, 11, 1), date(2026, 11, 30)):
            await repository.add(lancamento(dono, conta, dia))
        await repository.add(lancamento(dono, conta, date(2026, 12, 1)))

        lidas = await repository.list_between(dono, NOVEMBRO)

        assert [t.occurred_on for t in lidas] == [date(2026, 11, 1), date(2026, 11, 30)]

    async def test_vem_da_mais_antiga_para_a_mais_recente(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        for dia in (20, 5, 12):
            await repository.add(lancamento(dono, conta, date(2026, 11, dia)))

        lidas = await repository.list_between(dono, NOVEMBRO)

        assert [t.occurred_on.day for t in lidas] == [5, 12, 20]

    async def test_ninguem_ve_as_transacoes_de_outra_pessoa(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta_do_outro: AccountId,
    ) -> None:
        await repository.add(lancamento(outro_dono, conta_do_outro, date(2026, 11, 7)))

        assert await repository.list_between(dono, NOVEMBRO) == []

    async def test_totais_antes_do_dia_somam_so_o_que_veio_antes(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        for dia, kind, cents in (
            (date(2026, 10, 5), RECEITA, 500000),
            (date(2026, 10, 20), DESPESA, 4590),
            (date(2026, 10, 31), DESPESA, 410),
            (date(2026, 11, 1), DESPESA, 99999),
        ):
            await repository.add(lancamento(dono, conta, dia, kind, cents))

        totais = await repository.totals_before(dono, date(2026, 11, 1))

        assert totais == Totals(income_cents=500000, expense_cents=5000)

    async def test_totais_nao_somam_transacoes_de_outra_pessoa(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta_do_outro: AccountId,
    ) -> None:
        await repository.add(lancamento(outro_dono, conta_do_outro, date(2026, 10, 5)))

        assert await repository.totals_before(dono, date(2026, 11, 1)) == Totals()

    async def test_totais_por_conta_separam_cada_conta_do_dono(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
        conta_do_outro: AccountId,
    ) -> None:
        dia = date(2026, 11, 7)
        await repository.add(lancamento(dono, conta, dia, RECEITA, 500000))
        await repository.add(lancamento(dono, conta, dia, DESPESA, 4590))
        await repository.add(lancamento(dono, outra_conta, dia, DESPESA, 15000))
        await repository.add(lancamento(outro_dono, conta_do_outro, dia, RECEITA, 999))

        totais = await repository.totals_by_account(dono)

        assert totais == {
            conta: Totals(income_cents=500000, expense_cents=4590),
            outra_conta: Totals(income_cents=0, expense_cents=15000),
        }

    async def test_totais_por_conta_de_quem_nao_lancou_nada(
        self, repository: TransactionRepository, dono: OwnerId
    ) -> None:
        assert await repository.totals_by_account(dono) == {}

    async def test_o_extrato_pode_ser_de_uma_conta_so(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
    ) -> None:
        da_conta = lancamento(dono, conta, date(2026, 11, 7))
        await repository.add(da_conta)
        await repository.add(lancamento(dono, outra_conta, date(2026, 11, 8)))

        lidas = await repository.list_between(dono, NOVEMBRO, account=conta)

        assert [t.id for t in lidas] == [da_conta.id]

    async def test_os_totais_anteriores_podem_ser_de_uma_conta_so(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
    ) -> None:
        await repository.add(lancamento(dono, conta, date(2026, 10, 5), RECEITA, 1000))
        await repository.add(
            lancamento(dono, outra_conta, date(2026, 10, 5), RECEITA, 7)
        )

        totais = await repository.totals_before(dono, date(2026, 11, 1), account=conta)

        assert totais == Totals(income_cents=1000, expense_cents=0)

    async def test_get_traz_a_transacao_do_dono(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        gravada = lancamento(dono, conta, date(2026, 11, 7))
        await repository.add(gravada)

        lida = await repository.get(dono, gravada.id)

        assert lida is not None
        assert lida.id == gravada.id
        assert lida.amount == gravada.amount

    async def test_get_nao_traz_a_transacao_de_outra_pessoa(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta_do_outro: AccountId,
    ) -> None:
        do_outro = lancamento(outro_dono, conta_do_outro, date(2026, 11, 7))
        await repository.add(do_outro)

        assert await repository.get(dono, do_outro.id) is None
        assert await repository.get(dono, TransactionId.new()) is None

    async def test_update_grava_os_dados_corrigidos(
        self,
        repository: TransactionRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
    ) -> None:
        gravada = lancamento(dono, conta, date(2026, 11, 7))
        await repository.add(gravada)
        lida = await repository.get(dono, gravada.id)
        assert lida is not None

        lida.revise(
            account=outra_conta,
            kind=RECEITA,
            amount=Money(99900),
            description=Description("Reembolso"),
            category=Category("salario"),
            occurred_on=date(2026, 11, 9),
        )
        await repository.update(lida)

        corrigida = await repository.get(dono, gravada.id)
        assert corrigida is not None
        assert corrigida.account == outra_conta
        assert corrigida.kind is RECEITA
        assert corrigida.amount == Money(99900)
        assert corrigida.description == Description("Reembolso")
        assert corrigida.category == Category("salario")
        assert corrigida.occurred_on == date(2026, 11, 9)

    async def test_mudar_o_objeto_lido_sem_update_nao_grava_nada(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        gravada = lancamento(dono, conta, date(2026, 11, 7), cents=1250)
        await repository.add(gravada)
        lida = await repository.get(dono, gravada.id)
        assert lida is not None

        lida.amount = Money(1)

        relida = await repository.get(dono, gravada.id)
        assert relida is not None
        assert relida.amount == Money(1250)

    async def test_update_nao_mexe_nas_outras(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        corrigida = lancamento(dono, conta, date(2026, 11, 7), cents=1250)
        intocada = lancamento(dono, conta, date(2026, 11, 8), cents=1250)
        await repository.add(corrigida)
        await repository.add(intocada)

        corrigida.amount = Money(5000)
        await repository.update(corrigida)

        lida = await repository.get(dono, intocada.id)
        assert lida is not None
        assert lida.amount == Money(1250)

    async def test_remove_apaga_so_a_transacao(
        self, repository: TransactionRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        apagada = lancamento(dono, conta, date(2026, 11, 7))
        mantida = lancamento(dono, conta, date(2026, 11, 8))
        await repository.add(apagada)
        await repository.add(mantida)

        await repository.remove(apagada)

        assert await repository.get(dono, apagada.id) is None
        assert [t.id for t in await repository.list_between(dono, NOVEMBRO)] == [
            mantida.id
        ]
