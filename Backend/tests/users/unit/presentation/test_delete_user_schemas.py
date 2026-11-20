import pytest
from pydantic import ValidationError

from app.users.presentation.api.v1.schemas.delete_user import DeleteUserRequest


def test_a_senha_do_pedido_nao_aparece_em_logs() -> None:
    pedido = DeleteUserRequest(password="S3nha!Forte123")

    assert "S3nha" not in repr(pedido)
    assert "S3nha" not in str(pedido)


@pytest.mark.parametrize("corpo", [{}, {"password": ""}, {"password": "a", "x": 1}])
def test_pedido_mal_formado_e_recusado(corpo: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DeleteUserRequest.model_validate(corpo)
