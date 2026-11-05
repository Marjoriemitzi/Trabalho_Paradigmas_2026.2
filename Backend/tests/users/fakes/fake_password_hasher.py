"""
Fake da porta PasswordHasher.
"""

from app.users.domain.value_objects.password import PasswordHash, RawPassword


class FakePasswordHasher:
    def hash(self, raw: RawPassword) -> PasswordHash:
        return PasswordHash(f"hash-falso:{raw.reveal()}")
