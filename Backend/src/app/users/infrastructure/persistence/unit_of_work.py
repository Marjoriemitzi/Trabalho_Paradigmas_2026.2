from app.shared.infrastructure.persistence.unit_of_work import (
    BaseSqlAlchemyUnitOfWork,
)
from app.users.application.ports.refresh_token_store import RefreshTokenStore
from app.users.domain.repositories.user_repository import UserRepository
from app.users.infrastructure.persistence.repositories.sql_refresh_token_store import (
    SqlRefreshTokenStore,
)
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)


class SqlAlchemyUnitOfWork(BaseSqlAlchemyUnitOfWork):
    @property
    def users(self) -> UserRepository:
        return SqlUserRepository(self._open_session())

    @property
    def refresh_tokens(self) -> RefreshTokenStore:
        return SqlRefreshTokenStore(self._open_session())
