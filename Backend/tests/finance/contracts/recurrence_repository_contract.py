from datetime import date

import pytest

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.repositories.recurrence_repository import (
    RecurrenceRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind


def recorrencia(
    dono: OwnerId,
    conta: AccountId,
    descricao: str = "Aluguel",
    categoria: str | None = "moradia",
    *,
    comeca_em: date = date(2026, 12, 1),
    termina_em: date | None = None,
) -> Recurrence:
    return Recurrence.create(
        owner=dono,
        account=conta,
        kind=TransactionKind.EXPENSE,
        amount=Money(150000),
        description=Description(descricao),
        category=None if categoria is None else Category(categoria),
        schedule=Schedule(Frequency.MONTHLY, 5),
        window=ActiveRange(comeca_em, termina_em),
    )


class RecurrenceRepositoryContract:
    @pytest.fixture
    def repository(self) -> RecurrenceRepository:
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
    def conta_do_outro(self, outro_dono: OwnerId) -> AccountId:
        raise NotImplementedError

    async def test_adiciona_e_busca_com_todos_os_dados(
        self, repository: RecurrenceRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        gravada = recorrencia(dono, conta, termina_em=date(2027, 5, 31))
        await repository.add(gravada)

        lida = await repository.get(dono, gravada.id)

        assert lida is not None
        assert lida.id == gravada.id
        assert lida.owner == dono
        assert lida.account == conta
        assert lida.kind is TransactionKind.EXPENSE
        assert lida.amount == Money(150000)
        assert lida.description == Description("Aluguel")
        assert lida.category == Category("moradia")
        assert lida.schedule == Schedule(Frequency.MONTHLY, 5)
        assert lida.starts_on == date(2026, 12, 1)
        assert lida.ends_on == date(2027, 5, 31)

    async def test_categoria_e_fim_nulos_sao_aceitos(
        self, repository: RecurrenceRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        gravada = recorrencia(dono, conta, categoria=None)
        await repository.add(gravada)

        lida = await repository.get(dono, gravada.id)

        assert lida is not None
        assert lida.category is None
        assert lida.ends_on is None

    async def test_buscar_a_de_outra_pessoa_ou_inexistente_devolve_none(
        self,
        repository: RecurrenceRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta_do_outro: AccountId,
    ) -> None:
        da_outra = recorrencia(outro_dono, conta_do_outro)
        await repository.add(da_outra)

        assert await repository.get(dono, da_outra.id) is None
        assert await repository.get(dono, RecurrenceId.new()) is None

    async def test_lista_so_as_da_pessoa(
        self,
        repository: RecurrenceRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta: AccountId,
        conta_do_outro: AccountId,
    ) -> None:
        minha = recorrencia(dono, conta, "Aluguel")
        await repository.add(minha)
        await repository.add(recorrencia(outro_dono, conta_do_outro, "Alheia"))

        lidas = await repository.list_by_owner(dono)

        assert [r.id for r in lidas] == [minha.id]

    async def test_update_troca_a_regra_inteira(
        self, repository: RecurrenceRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        gravada = recorrencia(dono, conta)
        await repository.add(gravada)
        gravada.revise(
            account=conta,
            kind=TransactionKind.INCOME,
            amount=Money(900000),
            description=Description("Salário"),
            category=None,
            schedule=Schedule(Frequency.WEEKLY, 1),
            window=ActiveRange(date(2026, 12, 7), date(2027, 1, 31)),
        )

        await repository.update(gravada)

        lida = await repository.get(dono, gravada.id)
        assert lida is not None
        assert lida.kind is TransactionKind.INCOME
        assert lida.amount == Money(900000)
        assert lida.description == Description("Salário")
        assert lida.category is None
        assert lida.schedule == Schedule(Frequency.WEEKLY, 1)
        assert lida.starts_on == date(2026, 12, 7)
        assert lida.ends_on == date(2027, 1, 31)

    async def test_remove_apaga_so_a_pedida(
        self, repository: RecurrenceRepository, dono: OwnerId, conta: AccountId
    ) -> None:
        apagada = recorrencia(dono, conta, "Apagada")
        mantida = recorrencia(dono, conta, "Mantida")
        await repository.add(apagada)
        await repository.add(mantida)

        await repository.remove(apagada)

        assert await repository.get(dono, apagada.id) is None
        assert await repository.get(dono, mantida.id) is not None
