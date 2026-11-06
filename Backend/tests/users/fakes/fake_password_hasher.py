from app.users.domain.value_objects.password import PasswordHash, RawPassword


class FakePasswordHasher:
    async def hash(self, raw: RawPassword) -> PasswordHash:
        return PasswordHash(f"hash-falso:{raw.reveal()}")
