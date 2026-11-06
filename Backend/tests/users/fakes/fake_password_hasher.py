from app.users.domain.value_objects.password import PasswordHash, RawPassword


class FakePasswordHasher:
    async def hash(self, raw: RawPassword) -> PasswordHash:
        return PasswordHash(f"hash-falso:{raw.reveal()}")

    async def verify(self, raw: RawPassword, hashed: PasswordHash) -> bool:
        return hashed.value == f"hash-falso:{raw.reveal()}"
