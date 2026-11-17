from datetime import date

import pytest

from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.repositories.transfer_repository import TransferRepository
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transfer_flows import TransferFlows
from app.finance.domain.value_objects.transfer_id import TransferId

NOVEMBRO = Period(date(2026, 11, 1), date(2026, 11, 30))


def transferir(
    dono: OwnerId,
    de: AccountId,
    para: AccountId,
    cents: int = 1000,
    dia: date = date(2026, 11, 10),
) -> Transfer:
    return Transfer.record(
        owner=dono,
        source=de,
        destination=para,
        amount=Money(cents),
        description=Description("Transferência"),
        occurred_on=dia,
    )


class TransferRepositoryContract:
    @pytest.fixture
    def repository(self) -> TransferRepository:
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
    def terceira_conta(self, dono: OwnerId) -> AccountId:
        raise NotImplementedError

    @pytest.fixture
    def contas_do_outro(self, outro_dono: OwnerId) -> tuple[AccountId, AccountId]:
        raise NotImplementedError

    async def test_get_traz_a_transferencia_com_todos_os_dados(
        self,
        repository: TransferRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
    ) -> None:
        gravada = transferir(dono, conta, outra_conta, 150000)
        await repository.add(gravada)

        lida = await repository.get(dono, gravada.id)

        assert lida is not None
        assert lida.id == gravada.id
        assert lida.owner == dono
        assert lida.source == conta
        assert lida.destination == outra_conta
        assert lida.amount == Money(150000)
        assert lida.description == Description("Transferência")
        assert lida.occurred_on == date(2026, 11, 10)

    async def test_get_nao_traz_a_de_outra_pessoa(
        self,
        repository: TransferRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        contas_do_outro: tuple[AccountId, AccountId],
    ) -> None:
        da_outra = transferir(outro_dono, *contas_do_outro)
        await repository.add(da_outra)

        assert await repository.get(dono, da_outra.id) is None
        assert await repository.get(dono, TransferId.new()) is None

    async def test_remove_apaga_so_a_transferencia(
        self,
        repository: TransferRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
    ) -> None:
        apagada = transferir(dono, conta, outra_conta)
        mantida = transferir(dono, conta, outra_conta)
        await repository.add(apagada)
        await repository.add(mantida)

        await repository.remove(apagada)

        assert await repository.get(dono, apagada.id) is None
        assert await repository.get(dono, mantida.id) is not None

    async def test_lista_as_que_entram_e_saem_da_conta_no_periodo(
        self,
        repository: TransferRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
        terceira_conta: AccountId,
    ) -> None:
        saiu = transferir(dono, conta, outra_conta, dia=date(2026, 11, 20))
        entrou = transferir(dono, terceira_conta, conta, dia=date(2026, 11, 1))
        for t in (
            saiu,
            entrou,
            transferir(dono, outra_conta, terceira_conta),
            transferir(dono, conta, outra_conta, dia=date(2026, 10, 31)),
            transferir(dono, conta, outra_conta, dia=date(2026, 12, 1)),
        ):
            await repository.add(t)

        lidas = await repository.list_between(dono, conta, NOVEMBRO)

        assert [t.id for t in lidas] == [entrou.id, saiu.id]

    async def test_fluxos_antes_do_dia_separam_entrada_e_saida(
        self,
        repository: TransferRepository,
        dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
        terceira_conta: AccountId,
    ) -> None:
        for t in (
            transferir(dono, outra_conta, conta, 50000, date(2026, 10, 5)),
            transferir(dono, conta, terceira_conta, 2000, date(2026, 10, 31)),
            transferir(dono, outra_conta, conta, 99999, date(2026, 11, 1)),
            transferir(dono, outra_conta, terceira_conta, 7, date(2026, 10, 5)),
        ):
            await repository.add(t)

        fluxos = await repository.flows_before(dono, conta, date(2026, 11, 1))

        assert fluxos == TransferFlows(incoming_cents=50000, outgoing_cents=2000)

    async def test_fluxos_por_conta_de_cada_conta_do_dono(
        self,
        repository: TransferRepository,
        dono: OwnerId,
        outro_dono: OwnerId,
        conta: AccountId,
        outra_conta: AccountId,
        terceira_conta: AccountId,
        contas_do_outro: tuple[AccountId, AccountId],
    ) -> None:
        for t in (
            transferir(dono, conta, outra_conta, 150000),
            transferir(dono, conta, terceira_conta, 20000),
            transferir(dono, terceira_conta, conta, 5000),
            transferir(outro_dono, *contas_do_outro, 999),
        ):
            await repository.add(t)

        fluxos = await repository.flows_by_account(dono)

        assert fluxos == {
            conta: TransferFlows(incoming_cents=5000, outgoing_cents=170000),
            outra_conta: TransferFlows(incoming_cents=150000, outgoing_cents=0),
            terceira_conta: TransferFlows(incoming_cents=20000, outgoing_cents=5000),
        }

    async def test_fluxos_por_conta_de_quem_nao_transferiu_nada(
        self, repository: TransferRepository, dono: OwnerId
    ) -> None:
        assert await repository.flows_by_account(dono) == {}
