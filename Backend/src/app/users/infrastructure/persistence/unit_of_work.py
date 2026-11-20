from app.shared.infrastructure.persistence.unit_of_work import (
    BaseSqlAlchemyUnitOfWork,
)
from app.users.application.ports.token_blocklist import TokenBlocklist
from app.users.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.users.domain.repositories.user_repository import UserRepository
from app.users.infrastructure.persistence.repositories.sql_refresh_token_repository import (  # noqa: E501
    SqlRefreshTokenRepository,
)
from app.users.infrastructure.persistence.repositories.sql_token_blocklist import (
    SqlTokenBlocklist,
)
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)


class SqlAlchemyUnitOfWork(BaseSqlAlchemyUnitOfWork):
    @property
    def users(self) -> UserRepository:
        return SqlUserRepository(self._open_session())

    @property
    def refresh_tokens(self) -> RefreshTokenRepository:
        return SqlRefreshTokenRepository(self._open_session())

    @property
    def token_blocklist(self) -> TokenBlocklist:
        return SqlTokenBlocklist(self._open_session())
