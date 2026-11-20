from dataclasses import dataclass
from typing import Protocol

from app.users.application.attempts import AttemptGuard
from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.application.session import Session, SessionIssuer
from app.users.domain.entities.user import User
from app.users.domain.exceptions import InvalidEmailError
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import RawPassword


class AuthenticateUserInputPort(Protocol):
    async def execute(self, data: AuthenticateUserInput) -> None: ...


class AuthenticateUserOutputPort(Protocol):
    def present_authenticated(self, session: Session) -> None: ...

    def present_invalid_credentials(self) -> None: ...

    def present_too_many_attempts(self, retry_after: int) -> None: ...


@dataclass(frozen=True, slots=True)
class AuthenticateUserInteractor(AuthenticateUserInputPort):
    uow: UnitOfWork
    hasher: PasswordHasher
    issuer: SessionIssuer
    attempts: AttemptGuard
    presenter: AuthenticateUserOutputPort

    async def execute(self, data: AuthenticateUserInput) -> None:
        par, so_ip = self.attempts.login_rules(data.client_ip, data.email)
        espera = await self.attempts.retry_after((par, so_ip))
        if espera is not None:
            self.presenter.present_too_many_attempts(espera)
            return

        session = await self._authenticate(data)
        if session is None:
            await self.attempts.record((par, so_ip))
            self.presenter.present_invalid_credentials()
            return
        await self.attempts.reset((par,))
        self.presenter.present_authenticated(session)

    async def _authenticate(self, data: AuthenticateUserInput) -> Session | None:
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
            if not await self.hasher.verify(senha, user.password_hash):
                return None
            return await self._open_session(user)

    async def _open_session(self, user: User) -> Session:
        session = await self.issuer.issue(self.uow, user)
        await self.uow.commit()
        return session
