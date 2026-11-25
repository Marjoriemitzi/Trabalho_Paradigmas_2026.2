from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.attempts import AttemptGuard
from app.users.application.ports.clock import Clock
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.session import SessionIssuer
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInputPort,
    AuthenticateUserInteractor,
    AuthenticateUserOutputPort,
)
from app.users.application.use_cases.change_password import (
    ChangePasswordInputPort,
    ChangePasswordInteractor,
    ChangePasswordOutputPort,
)
from app.users.application.use_cases.delete_user import (
    DeleteUserInputPort,
    DeleteUserInteractor,
    DeleteUserOutputPort,
)
from app.users.application.use_cases.get_current_user import (
    GetCurrentUserInputPort,
    GetCurrentUserInteractor,
    GetCurrentUserOutputPort,
)
from app.users.application.use_cases.logout import (
    LogoutInputPort,
    LogoutInteractor,
    LogoutOutputPort,
)
from app.users.application.use_cases.refresh_session import (
    RefreshSessionInputPort,
    RefreshSessionInteractor,
    RefreshSessionOutputPort,
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
from app.users.presentation.api.v1.controllers.change_password_controller import (
    ChangePasswordFactory,
)
from app.users.presentation.api.v1.controllers.delete_user_controller import (
    DeleteUserFactory,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserFactory,
)
from app.users.presentation.api.v1.controllers.logout_controller import (
    LogoutFactory,
)
from app.users.presentation.api.v1.controllers.refresh_session_controller import (
    RefreshSessionFactory,
)
from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserFactory,
)


def register_user_factory(
    session_factory: async_sessionmaker[AsyncSession],
    hasher: PasswordHasher,
    policy: PasswordPolicy,
    attempts: AttemptGuard,
) -> RegisterUserFactory:
    def build(presenter: RegisterUserOutputPort) -> RegisterUserInputPort:
        return RegisterUserInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            hasher=hasher,
            policy=policy,
            attempts=attempts,
            presenter=presenter,
        )

    return build


def authenticate_user_factory(
    session_factory: async_sessionmaker[AsyncSession],
    hasher: PasswordHasher,
    issuer: SessionIssuer,
    attempts: AttemptGuard,
) -> AuthenticateUserFactory:
    def build(presenter: AuthenticateUserOutputPort) -> AuthenticateUserInputPort:
        return AuthenticateUserInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            hasher=hasher,
            issuer=issuer,
            attempts=attempts,
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


def change_password_factory(
    session_factory: async_sessionmaker[AsyncSession],
    hasher: PasswordHasher,
    policy: PasswordPolicy,
    clock: Clock,
) -> ChangePasswordFactory:
    def build(presenter: ChangePasswordOutputPort) -> ChangePasswordInputPort:
        return ChangePasswordInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            hasher=hasher,
            policy=policy,
            clock=clock,
            presenter=presenter,
        )

    return build


def delete_user_factory(
    session_factory: async_sessionmaker[AsyncSession], hasher: PasswordHasher
) -> DeleteUserFactory:
    def build(presenter: DeleteUserOutputPort) -> DeleteUserInputPort:
        return DeleteUserInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            hasher=hasher,
            presenter=presenter,
        )

    return build


def refresh_session_factory(
    session_factory: async_sessionmaker[AsyncSession],
    issuer: SessionIssuer,
    clock: Clock,
) -> RefreshSessionFactory:
    def build(presenter: RefreshSessionOutputPort) -> RefreshSessionInputPort:
        return RefreshSessionInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            issuer=issuer,
            clock=clock,
            presenter=presenter,
        )

    return build


def logout_factory(
    session_factory: async_sessionmaker[AsyncSession], clock: Clock
) -> LogoutFactory:
    def build(presenter: LogoutOutputPort) -> LogoutInputPort:
        return LogoutInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), clock=clock, presenter=presenter
        )

    return build
