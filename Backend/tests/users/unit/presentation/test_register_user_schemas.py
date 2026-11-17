from app.users.presentation.api.v1.schemas.register_user import RegisterUserRequest


def test_a_senha_do_pedido_nao_aparece_em_logs() -> None:
    pedido = RegisterUserRequest(email="ana@acme.com", password="S3nha!Forte123")
    assert "S3nha" not in repr(pedido)
    assert "S3nha" not in str(pedido)
