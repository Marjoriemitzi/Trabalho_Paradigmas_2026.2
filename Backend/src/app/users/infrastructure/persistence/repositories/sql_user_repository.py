from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.domain.entities.user import User
from app.users.domain.exceptions import EmailAlreadyRegisteredError
from app.users.domain.value_objects.email import Email
from app.users.infrastructure.persistence.mappers.user_mapper import (
    to_entity,
    to_model,
)
from app.users.infrastructure.persistence.models.user_model import UserModel

EMAIL_UNICO = "uq_users_email"


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(to_model(user))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if f'"{EMAIL_UNICO}"' in str(error.orig):
                raise EmailAlreadyRegisteredError(user.email.value) from error
            raise

    async def exists(self, email: Email) -> bool:
        consulta = select(UserModel.id).where(UserModel.email == email.value)
        return await self._session.scalar(consulta) is not None

    async def get_by_email(self, email: Email) -> User | None:
        consulta = select(UserModel).where(UserModel.email == email.value)
        modelo = await self._session.scalar(consulta)
        return None if modelo is None else to_entity(modelo)
