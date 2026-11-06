"""
Porta para gerar o hash de uma senha.
"""

from typing import Protocol

from app.users.domain.value_objects.password import PasswordHash, RawPassword


class PasswordHasher(Protocol):
    async def hash(self, raw: RawPassword) -> PasswordHash: ...
