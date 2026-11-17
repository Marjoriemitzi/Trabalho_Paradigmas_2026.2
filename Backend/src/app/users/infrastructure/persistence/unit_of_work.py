# mypy: ignore-errors
from app.shared.infrastructure.persistence.unit_of_work import BaseSqlAlchemyUnitOfWork
from app.users.application.ports.token_blocklist import TokenBlocklist
from app.users.domain.repositories.user_repository import UserRepository
from app.users.infrastructure.persistence.repositories.sql_token_blocklist import SqlTokenBlocklist
from app.users.infrastructure.persistence.repositories.sql_user_repository import SqlUserRepository

class SqlAlchemyUnitOfWork(BaseSqlAlchemyUnitOfWork):
    @property
    def users(self) -> UserRepository:
        return SqlUserRepository(self._open_session())

    @property
    def token_blocklist(self) -> TokenBlocklist:
        return SqlTokenBlocklist(self._open_session())
