from app.users.domain.exceptions import WeakPasswordError


class FakePasswordPolicy:
    def __init__(self, rejects: dict[str, list[str]] | None = None) -> None:
        self._rejects = rejects or {}

    def check(self, password: str) -> None:
        if password in self._rejects:
            raise WeakPasswordError(self._rejects[password])
