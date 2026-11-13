import pytest

from app.users.domain.value_objects.password import PasswordHash, RawPassword

HASH = "$argon2id$v=19$m=65536,t=3,p=4$c2FsdA$aGFzaA"


def test_raw_password_guarda_a_senha() -> None:
    assert RawPassword("S3nha!Forte123").reveal() == "S3nha!Forte123"


def test_raw_password_nao_aparece_em_repr_nem_str() -> None:
    senha = RawPassword("S3nha!Forte123")
    assert "S3nha" not in repr(senha)
    assert "S3nha" not in str(senha)


def test_raw_password_recusa_texto_vazio() -> None:
    with pytest.raises(ValueError, match="vazia"):
        RawPassword("")


def test_password_hash_guarda_o_hash() -> None:
    assert PasswordHash(HASH).value == HASH


def test_password_hash_recusa_texto_vazio() -> None:
    with pytest.raises(ValueError, match="vazio"):
        PasswordHash("")


def test_password_hash_nao_aparece_em_repr() -> None:
    assert HASH not in repr(PasswordHash(HASH))
