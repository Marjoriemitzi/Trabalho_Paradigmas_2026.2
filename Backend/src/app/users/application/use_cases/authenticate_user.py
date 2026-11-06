from dataclasses import dataclass
from typing import Protocol

from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.token_issuer import AccessToken, TokenIssuer
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.entities.user import User
from app.users.domain.exceptions import InvalidEmailError
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import RawPassword


class AuthenticateUserInputPort(Protocol):
    async def execute(self, data: AuthenticateUserInput) -> None: ...


class AuthenticateUserOutputPort(Protocol):
    def present_authenticated(self, token: AccessToken) -> None: ...

    def present_invalid_credentials(self) -> None: ...


@dataclass(frozen=True, slots=True)
class AuthenticateUserInteractor(AuthenticateUserInputPort):
    uow: UnitOfWork
    hasher: PasswordHasher
    tokens: TokenIssuer
    presenter: AuthenticateUserOutputPort

    async def execute(self, data: AuthenticateUserInput) -> None:
        user = await self._authenticate(data)
        if user is None:
            self.presenter.present_invalid_credentials()
            return
        self.presenter.present_authenticated(self.tokens.issue(user))

    async def _authenticate(self, data: AuthenticateUserInput) -> User | None:
        if not data.password:
            return None
        try:
            email = Email(data.email)
        except InvalidEmailError:
            return None

        senha = RawPassword(data.password)
        async with self.uow:
            user = await self.uow.users.get_by_email(email)

        if user is None:
            await self.hasher.hash(senha)
            return None
        return user if await self.hasher.verify(senha, user.password_hash) else None
