import asyncio

from argon2 import PasswordHasher as Argon2

from app.users.domain.value_objects.password import PasswordHash, RawPassword


class Argon2Hasher:
    def __init__(self) -> None:
        self._argon2 = Argon2()

    async def hash(self, raw: RawPassword) -> PasswordHash:
        gerado = await asyncio.to_thread(self._argon2.hash, raw.reveal())
        return PasswordHash(gerado)
