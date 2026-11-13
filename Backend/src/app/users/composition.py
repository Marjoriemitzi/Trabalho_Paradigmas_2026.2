from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.token_issuer import TokenIssuer
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInputPort,
    AuthenticateUserInteractor,
    AuthenticateUserOutputPort,
)
from app.users.application.use_cases.get_current_user import (
    GetCurrentUserInputPort,
    GetCurrentUserInteractor,
    GetCurrentUserOutputPort,
)
from app.users.application.use_cases.register_user import (
    RegisterUserInputPort,
    RegisterUserInteractor,
    RegisterUserOutputPort,
)
from app.users.domain.services.password_policy import PasswordPolicy
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserFactory,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserFactory,
)
from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserFactory,
)


def register_user_factory(
    session_factory: async_sessionmaker[AsyncSession],
    hasher: PasswordHasher,
    policy: PasswordPolicy,
) -> RegisterUserFactory:
    def build(presenter: RegisterUserOutputPort) -> RegisterUserInputPort:
        return RegisterUserInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            hasher=hasher,
            policy=policy,
            presenter=presenter,
        )

    return build


def authenticate_user_factory(
    session_factory: async_sessionmaker[AsyncSession],
    hasher: PasswordHasher,
    tokens: TokenIssuer,
) -> AuthenticateUserFactory:
    def build(presenter: AuthenticateUserOutputPort) -> AuthenticateUserInputPort:
        return AuthenticateUserInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            hasher=hasher,
            tokens=tokens,
            presenter=presenter,
        )

    return build


def get_current_user_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> GetCurrentUserFactory:
    def build(presenter: GetCurrentUserOutputPort) -> GetCurrentUserInputPort:
        return GetCurrentUserInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build
