from app.shared.infrastructure.persistence.unit_of_work import (
    BaseSqlAlchemyUnitOfWork,
)
from app.users.domain.repositories.user_repository import UserRepository
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)


class SqlAlchemyUnitOfWork(BaseSqlAlchemyUnitOfWork):
    @property
    def users(self) -> UserRepository:
        return SqlUserRepository(self._open_session())
