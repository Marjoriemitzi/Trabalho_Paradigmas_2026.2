import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.repositories.recurrence_repository import (
    RecurrenceRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.repositories.sql_recurrence_repository import (  # noqa: E501
    SqlRecurrenceRepository,
)
from tests.finance.contracts.recurrence_repository_contract import (
    RecurrenceRepositoryContract,
)
from tests.finance.integration.conftest import NovaConta, NovoDono


class TestSqlRecurrenceRepository(RecurrenceRepositoryContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> RecurrenceRepository:
        return SqlRecurrenceRepository(session)

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
    async def conta_do_outro(
        self, nova_conta: NovaConta, outro_dono: OwnerId
    ) -> AccountId:
        return await nova_conta(outro_dono)
