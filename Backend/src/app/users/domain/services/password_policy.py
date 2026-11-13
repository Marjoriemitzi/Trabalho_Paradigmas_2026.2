from typing import Protocol


class PasswordPolicy(Protocol):
    def check(self, password: str) -> None: ...
