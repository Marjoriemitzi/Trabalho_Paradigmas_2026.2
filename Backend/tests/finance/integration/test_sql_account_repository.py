import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.account import Account
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.repositories.sql_account_repository import (
    SqlAccountRepository,
)
from tests.finance.contracts.account_repository_contract import (
    AccountRepositoryContract,
)
from tests.finance.integration.conftest import NovoDono


class TestSqlAccountRepository(AccountRepositoryContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> AccountRepository:
        return SqlAccountRepository(session)

    @pytest.fixture
    async def dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def outro_dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()


async def test_outro_erro_de_integridade_nao_vira_nome_repetido(
    session: AsyncSession,
) -> None:
    sem_dono = Account.open(
        OwnerId(uuid.uuid4()), AccountName("Carteira"), AccountKind.WALLET
    )

    with pytest.raises(IntegrityError, match="fk_accounts_owner_id_users"):
        await SqlAccountRepository(session).add(sem_dono)
