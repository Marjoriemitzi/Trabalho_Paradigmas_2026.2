import pytest

from app.users.domain.value_objects.password import RawPassword


def test_raw_password_guarda_a_senha() -> None:
    assert RawPassword("S3nha!Forte123").reveal() == "S3nha!Forte123"


def test_raw_password_nao_aparece_em_repr_nem_str() -> None:
    senha = RawPassword("S3nha!Forte123")
    assert "S3nha" not in repr(senha)
    assert "S3nha" not in str(senha)


def test_raw_password_recusa_texto_vazio() -> None:
    with pytest.raises(ValueError, match="vazia"):
        RawPassword("")
