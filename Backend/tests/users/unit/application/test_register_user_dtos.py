from app.users.application.dtos.register_user import RegisterUserInput


def test_a_senha_do_pedido_nao_aparece_em_logs() -> None:
    pedido = RegisterUserInput(email="ana@acme.com", password="S3nha!Forte123")
    assert "S3nha" not in repr(pedido)
