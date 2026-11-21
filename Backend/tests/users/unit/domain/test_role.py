import pytest

from app.users.domain.value_objects.role import Role


def test_role_user_tem_valor_esperado() -> None:
    papel: str = Role.USER
    assert papel == "user"
    assert Role.USER.value == "user"
    assert Role("user") is Role.USER


@pytest.mark.parametrize("invalido", ["USER", "", "admin"])
def test_role_desconhecido_e_recusado(invalido: str) -> None:
    with pytest.raises(ValueError, match="is not a valid Role"):
        Role(invalido)
