from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import AccountNameTakenError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.mappers.account_mapper import (
    to_entity,
    to_model,
)
from app.finance.infrastructure.persistence.models.account_model import AccountModel

NOME_UNICO = "uq_accounts_owner_id_lower_name"


class SqlAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, account: Account) -> None:
        self._session.add(to_model(account))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if f'"{NOME_UNICO}"' in str(error.orig):
                raise AccountNameTakenError(account.name.text) from error
            raise

    async def list_by_owner(self, owner: OwnerId) -> list[Account]:
        consulta = (
            select(AccountModel)
            .where(AccountModel.owner_id == owner.value)
            .order_by(func.lower(AccountModel.name))
        )
        return [to_entity(m) for m in await self._session.scalars(consulta)]

    async def get(self, owner: OwnerId, account_id: AccountId) -> Account | None:
        consulta = select(AccountModel).where(
            AccountModel.id == account_id.value,
            AccountModel.owner_id == owner.value,
        )
        modelo = await self._session.scalar(consulta)
        return None if modelo is None else to_entity(modelo)
