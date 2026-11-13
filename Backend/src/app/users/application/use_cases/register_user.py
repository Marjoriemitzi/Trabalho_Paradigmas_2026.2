from dataclasses import dataclass
from typing import Protocol

from app.users.application.dtos.register_user import RegisteredUser, RegisterUserInput
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.entities.user import User
from app.users.domain.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
    WeakPasswordError,
)
from app.users.domain.services.password_policy import PasswordPolicy
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import RawPassword


class RegisterUserInputPort(Protocol):
    async def execute(self, data: RegisterUserInput) -> None: ...


class RegisterUserOutputPort(Protocol):
    def present_registered(self, user: RegisteredUser) -> None: ...

    def present_email_taken(self, email: str) -> None: ...

    def present_weak_password(self, reasons: list[str]) -> None: ...

    def present_invalid_email(self, email: str) -> None: ...


@dataclass(frozen=True, slots=True)
class RegisterUserInteractor(RegisterUserInputPort):
    uow: UnitOfWork
    hasher: PasswordHasher
    policy: PasswordPolicy
    presenter: RegisterUserOutputPort

    async def execute(self, data: RegisterUserInput) -> None:
        try:
            email = Email(data.email)
            self.policy.check(data.password)
        except InvalidEmailError as error:
            self.presenter.present_invalid_email(error.value)
            return
        except WeakPasswordError as error:
            self.presenter.present_weak_password(error.reasons)
            return

        password_hash = await self.hasher.hash(RawPassword(data.password))

        try:
            async with self.uow:
                if await self.uow.users.exists(email):
                    self.presenter.present_email_taken(email.value)
                    return
                user = User.register(email, password_hash)
                await self.uow.users.add(user)
                await self.uow.commit()
        except EmailAlreadyRegisteredError:
            self.presenter.present_email_taken(email.value)
            return

        self.presenter.present_registered(RegisteredUser.from_user(user))
