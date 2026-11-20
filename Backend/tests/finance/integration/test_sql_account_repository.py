import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import AccountInUseError
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.repositories.sql_account_repository import (
    SqlAccountRepository,
)
from app.finance.infrastructure.persistence.repositories.sql_transaction_repository import (  # noqa: E501
    SqlTransactionRepository,
)
from tests.finance.contracts.account_repository_contract import (
    AccountRepositoryContract,
    conta,
)
from tests.finance.contracts.transaction_repository_contract import lancamento
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


async def test_o_banco_recusa_apagar_conta_com_transacao_e_vira_conta_em_uso(
    session: AsyncSession, novo_dono: NovoDono
) -> None:
    dono = await novo_dono()
    repositorio = SqlAccountRepository(session)
    usada = conta(dono, "Usada")
    await repositorio.add(usada)
    await SqlTransactionRepository(session).add(
        lancamento(dono, usada.id, date(2026, 11, 10))
    )

    with pytest.raises(AccountInUseError):
        await repositorio.remove(usada)
