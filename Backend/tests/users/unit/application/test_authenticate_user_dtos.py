from app.users.application.dtos.authenticate_user import AuthenticateUserInput


def test_a_senha_do_pedido_nao_aparece_em_logs() -> None:
    pedido = AuthenticateUserInput(email="ana@acme.com", password="S3nha!Forte123")
    assert "S3nha" not in repr(pedido)
