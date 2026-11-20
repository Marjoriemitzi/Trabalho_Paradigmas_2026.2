import pytest
from pydantic import ValidationError

from app.users.presentation.api.v1.schemas.change_password import (
    ChangePasswordRequest,
)


def test_as_senhas_do_pedido_nao_aparecem_em_logs() -> None:
    pedido = ChangePasswordRequest(
        current_password="S3nha!Antiga123", new_password="N0va!SenhaForte"
    )

    assert "S3nha" not in repr(pedido)
    assert "N0va" not in str(pedido)


def test_campo_a_mais_e_recusado() -> None:
    with pytest.raises(ValidationError):
        ChangePasswordRequest.model_validate(
            {"current_password": "a", "new_password": "b", "extra": 1}
        )


def test_senha_atual_vazia_e_recusada() -> None:
    with pytest.raises(ValidationError):
        ChangePasswordRequest(current_password="", new_password="N0va!SenhaForte")
