import uuid
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId

NovoDono = Callable[[], Awaitable[OwnerId]]
NovaConta = Callable[[OwnerId], Awaitable[AccountId]]


@pytest.fixture
def novo_dono(connection: AsyncConnection) -> NovoDono:
    async def criar() -> OwnerId:
        user_id = uuid.uuid4()
        await connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, role)"
                " VALUES (:id, :email, 'hash', 'user')"
            ),
            {"id": user_id, "email": f"{user_id.hex}@acme.com"},
        )
        return OwnerId(user_id)

    return criar


@pytest.fixture
def nova_conta(connection: AsyncConnection) -> NovaConta:
    async def criar(dono: OwnerId) -> AccountId:
        account_id = uuid.uuid4()
        await connection.execute(
            text(
                "INSERT INTO accounts (id, owner_id, name, kind)"
                " VALUES (:id, :owner_id, :name, 'wallet')"
            ),
            {"id": account_id, "owner_id": dono.value, "name": account_id.hex},
        )
        return AccountId(account_id)

    return criar


@pytest.fixture
async def dono(novo_dono: NovoDono) -> OwnerId:
    return await novo_dono()


@pytest.fixture
async def conta(nova_conta: NovaConta, dono: OwnerId) -> AccountId:
    return await nova_conta(dono)
