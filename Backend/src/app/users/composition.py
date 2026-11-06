from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.use_cases.register_user import (
    RegisterUserInputPort,
    RegisterUserInteractor,
    RegisterUserOutputPort,
)
from app.users.domain.services.password_policy import PasswordPolicy
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
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
