from app.users.presentation.api.v1.schemas.authenticate_user import (
    AuthenticateUserRequest,
)


def test_a_senha_do_pedido_nao_aparece_em_logs() -> None:
    pedido = AuthenticateUserRequest(email="ana@acme.com", password="S3nha!Forte123")
    assert "S3nha" not in repr(pedido)
