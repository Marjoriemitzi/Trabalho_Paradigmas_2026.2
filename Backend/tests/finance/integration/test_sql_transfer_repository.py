import uuid
from datetime import date

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.repositories.transfer_repository import TransferRepository
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.models.transfer_model import TransferModel
from app.finance.infrastructure.persistence.repositories.sql_transfer_repository import (  # noqa: E501
    SqlTransferRepository,
)
from tests.finance.contracts.transfer_repository_contract import (
    TransferRepositoryContract,
    transferir,
)
from tests.finance.integration.conftest import NovaConta, NovoDono


class TestSqlTransferRepository(TransferRepositoryContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> TransferRepository:
        return SqlTransferRepository(session)

    @pytest.fixture
    async def dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def outro_dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def outra_conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def terceira_conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def contas_do_outro(
        self, nova_conta: NovaConta, outro_dono: OwnerId
    ) -> tuple[AccountId, AccountId]:
        return await nova_conta(outro_dono), await nova_conta(outro_dono)


async def test_as_duas_contas_precisam_ser_do_mesmo_dono(
    session: AsyncSession,
    dono: OwnerId,
    conta: AccountId,
    novo_dono: NovoDono,
    nova_conta: NovaConta,
) -> None:
    conta_da_bia = await nova_conta(await novo_dono())

    with pytest.raises(
        IntegrityError, match="fk_transfers_to_account_id_owner_id_accounts"
    ):
        await SqlTransferRepository(session).add(transferir(dono, conta, conta_da_bia))


async def test_o_banco_recusa_a_mesma_conta_nos_dois_lados(
    session: AsyncSession, dono: OwnerId, conta: AccountId
) -> None:
    with pytest.raises(IntegrityError, match="ck_transfers_different_accounts"):
        await session.execute(
            insert(TransferModel).values(
                id=uuid.uuid4(),
                owner_id=dono.value,
                from_account_id=conta.value,
                to_account_id=conta.value,
                amount_cents=100,
                description="Ajuste",
                occurred_on=date(2026, 11, 10),
            )
        )
