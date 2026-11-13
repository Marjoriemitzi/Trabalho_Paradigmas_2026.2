from datetime import date

import pytest

from app.finance.application.ports.spending_reader import SpendingReader
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_total import CategoryTotal
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transaction_kind import TransactionKind

NOVEMBRO = Period(date(2026, 11, 1), date(2026, 11, 30))
RECEITA, DESPESA = TransactionKind.INCOME, TransactionKind.EXPENSE


def lancamento(
    dono: OwnerId,
    conta: AccountId,
    categoria: str,
    cents: int,
    dia: date = date(2026, 11, 7),
    kind: TransactionKind = DESPESA,
) -> Transaction:
    return Transaction.record(
        owner=dono,
        account=conta,
        kind=kind,
        amount=Money(cents),
        description=Description("Lançamento"),
        category=Category(categoria),
        occurred_on=dia,
    )


class SpendingReaderContract:
    @pytest.fixture
    def repository(self) -> TransactionRepository:
        raise NotImplementedError

    @pytest.fixture
    def reader(self, repository: TransactionRepository) -> SpendingReader:
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

    async def test_sem_lancamentos_a_lista_e_vazia(
        self, reader: SpendingReader, dono: OwnerId
    ) -> None:
        assert await reader.by_category(dono, DESPESA, NOVEMBRO) == []

    async def test_soma_e_conta_cada_categoria_do_maior_para_o_menor(
        self,
        repository: TransactionRepository,
        reader: SpendingReader,
        dono: OwnerId,
        conta: AccountId,
    ) -> None:
        for categoria, cents in (
            ("mercado", 4590),
            ("lazer", 3000),
            ("mercado", 12000),
            ("transporte", 3000),
        ):
            await repository.add(lancamento(dono, conta, categoria, cents))

        totais = await reader.by_category(dono, DESPESA, NOVEMBRO)

        assert totais == [
            CategoryTotal(Category("mercado"), 16590, 2),
            CategoryTotal(Category("lazer"), 3000, 1),
            CategoryTotal(Category("transporte"), 3000, 1),
        ]

    async def test_so_o_tipo_pedido_entra(
        self,
        repository: TransactionRepository,
        reader: SpendingReader,
        dono: OwnerId,
        conta: AccountId,
    ) -> None:
        await repository.add(lancamento(dono, conta, "mercado", 4590))
        await repository.add(lancamento(dono, conta, "salario", 500000, kind=RECEITA))

        receitas = await reader.by_category(dono, RECEITA, NOVEMBRO)

        assert receitas == [CategoryTotal(Category("salario"), 500000, 1)]

    async def test_so_o_periodo_entra_com_os_dois_dias_das_pontas(
        self,
        repository: TransactionRepository,
        reader: SpendingReader,
        dono: OwnerId,
        conta: AccountId,
    ) -> None:
        for dia in (
            date(2026, 10, 31),
            date(2026, 11, 1),
            date(2026, 11, 30),
            date(2026, 12, 1),
        ):
            await repository.add(lancamento(dono, conta, "mercado", 100, dia))

        totais = await reader.by_category(dono, DESPESA, NOVEMBRO)

        assert totais == [CategoryTotal(Category("mercado"), 200, 2)]

    async def test_nao_soma_lancamentos_de_outra_pessoa(
        self,
        repository: TransactionRepository,
        reader: SpendingReader,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta_do_outro: AccountId,
    ) -> None:
        await repository.add(lancamento(outro_dono, conta_do_outro, "mercado", 4590))

        assert await reader.by_category(dono, DESPESA, NOVEMBRO) == []

    async def test_pode_ser_de_uma_conta_so(
        self,
        repository: TransactionRepository,
        reader: SpendingReader,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
    ) -> None:
        await repository.add(lancamento(dono, conta, "mercado", 4590))
        await repository.add(lancamento(dono, outra_conta, "mercado", 7))

        totais = await reader.by_category(dono, DESPESA, NOVEMBRO, account=conta)

        assert totais == [CategoryTotal(Category("mercado"), 4590, 1)]
