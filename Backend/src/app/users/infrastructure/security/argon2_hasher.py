import asyncio

from argon2 import PasswordHasher as Argon2
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.users.domain.value_objects.password import PasswordHash, RawPassword


class Argon2Hasher:
    def __init__(self) -> None:
        self._argon2 = Argon2()

    async def hash(self, raw: RawPassword) -> PasswordHash:
        gerado = await asyncio.to_thread(self._argon2.hash, raw.reveal())
        return PasswordHash(gerado)

    async def verify(self, raw: RawPassword, hashed: PasswordHash) -> bool:
        try:
            return await asyncio.to_thread(
                self._argon2.verify, hashed.value, raw.reveal()
            )
        except (VerifyMismatchError, InvalidHashError):
            return False
