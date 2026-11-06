"""Testes do fake da porta PasswordHasher."""

from app.users.application.ports.password_hasher import PasswordHasher
from app.users.domain.value_objects.password import PasswordHash, RawPassword
from tests.users.fakes.fake_password_hasher import FakePasswordHasher


async def test_gera_um_hash_previsivel() -> None:
    hasher = FakePasswordHasher()
    assert await hasher.hash(RawPassword("S3nha!Forte123")) == PasswordHash(
        "hash-falso:S3nha!Forte123"
    )


def test_fake_cumpre_a_porta() -> None:
    porta: PasswordHasher = FakePasswordHasher()
    assert porta is not None
