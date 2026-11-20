from typing import Protocol


class RefreshTokenGenerator(Protocol):
    def generate(self) -> str: ...
