import asyncio

from argon2 import PasswordHasher as Argon2

from app.users.domain.value_objects.password import PasswordHash, RawPassword


class Argon2Hasher:
    def __init__(self) -> None:
        self._argon2 = Argon2()

    async def hash(self, raw: RawPassword) -> PasswordHash:
        # O Argon2 é lento de propósito; roda numa thread para liberar o event loop.
        gerado = await asyncio.to_thread(self._argon2.hash, raw.reveal())
        return PasswordHash(gerado)
