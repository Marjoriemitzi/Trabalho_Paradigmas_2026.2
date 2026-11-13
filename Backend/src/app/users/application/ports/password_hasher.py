from typing import Protocol

from app.users.domain.value_objects.password import PasswordHash, RawPassword


class PasswordHasher(Protocol):
    async def hash(self, raw: RawPassword) -> PasswordHash: ...

    async def verify(self, raw: RawPassword, hashed: PasswordHash) -> bool: ...
