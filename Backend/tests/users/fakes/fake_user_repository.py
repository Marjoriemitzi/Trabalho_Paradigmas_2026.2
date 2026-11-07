from app.users.domain.entities.user import User
from app.users.domain.exceptions import EmailAlreadyRegisteredError
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_email: dict[Email, User] = {}

    async def add(self, user: User) -> None:
        if user.email in self._by_email:
            raise EmailAlreadyRegisteredError(user.email.value)
        self._by_email[user.email] = user

    async def exists(self, email: Email) -> bool:
        return email in self._by_email

    async def get_by_email(self, email: Email) -> User | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: UserId) -> User | None:
        return next((u for u in self._by_email.values() if u.id == user_id), None)

    def stored(self, email: Email) -> User | None:
        return self._by_email.get(email)
