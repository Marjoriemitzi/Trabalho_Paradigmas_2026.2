import uuid
from datetime import date

import pytest

from app.finance.application.ports.account_usage import AccountUsage
from app.finance.domain.entities.account import Account
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.repositories.recurrence_repository import (
    RecurrenceRepository,
)
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.repositories.transfer_repository import TransferRepository
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.account_repository_contract import conta
from tests.finance.contracts.recurrence_repository_contract import recorrencia
from tests.finance.contracts.transaction_repository_contract import lancamento
from tests.finance.contracts.transfer_repository_contract import transferir

DIA = date(2026, 11, 10)


class AccountUsageContract:
    @pytest.fixture
    def usage(self) -> AccountUsage:
        raise NotImplementedError

    @pytest.fixture
    def accounts(self) -> AccountRepository:
        raise NotImplementedError

    @pytest.fixture
    def transactions(self) -> TransactionRepository:
        raise NotImplementedError

    @pytest.fixture
    def transfers(self) -> TransferRepository:
        raise NotImplementedError

    @pytest.fixture
    def recurrences(self) -> RecurrenceRepository:
        raise NotImplementedError

    @pytest.fixture
    def dono(self) -> OwnerId:
        raise NotImplementedError

    async def abrir(self, accounts: AccountRepository, dono: OwnerId) -> Account:
        nova = conta(dono, f"Conta {uuid.uuid4().hex}")
        await accounts.add(nova)
        return nova

    async def test_conta_vazia_nao_esta_em_uso(
        self, usage: AccountUsage, accounts: AccountRepository, dono: OwnerId
    ) -> None:
        vazia = await self.abrir(accounts, dono)

        assert await usage.in_use(dono, vazia) is False

    async def test_conta_com_transacao_esta_em_uso(
        self,
        usage: AccountUsage,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        dono: OwnerId,
    ) -> None:
        usada = await self.abrir(accounts, dono)
        await transactions.add(lancamento(dono, usada.id, DIA))

        assert await usage.in_use(dono, usada) is True

    async def test_conta_de_origem_de_uma_transferencia_esta_em_uso(
        self,
        usage: AccountUsage,
        accounts: AccountRepository,
        transfers: TransferRepository,
        dono: OwnerId,
    ) -> None:
        origem = await self.abrir(accounts, dono)
        destino = await self.abrir(accounts, dono)
        await transfers.add(transferir(dono, origem.id, destino.id))

        assert await usage.in_use(dono, origem) is True

    async def test_conta_de_destino_de_uma_transferencia_esta_em_uso(
        self,
        usage: AccountUsage,
        accounts: AccountRepository,
        transfers: TransferRepository,
        dono: OwnerId,
    ) -> None:
        origem = await self.abrir(accounts, dono)
        destino = await self.abrir(accounts, dono)
        await transfers.add(transferir(dono, origem.id, destino.id))

        assert await usage.in_use(dono, destino) is True

    async def test_a_transacao_de_outra_conta_nao_conta(
        self,
        usage: AccountUsage,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        dono: OwnerId,
    ) -> None:
        vazia = await self.abrir(accounts, dono)
        usada = await self.abrir(accounts, dono)
        await transactions.add(lancamento(dono, usada.id, DIA))

        assert await usage.in_use(dono, vazia) is False

    async def test_conta_com_recorrencia_esta_em_uso(
        self,
        usage: AccountUsage,
        accounts: AccountRepository,
        recurrences: RecurrenceRepository,
        dono: OwnerId,
    ) -> None:
        usada = await self.abrir(accounts, dono)
        await recurrences.add(recorrencia(dono, usada.id))

        assert await usage.in_use(dono, usada) is True
