import json

from app.shared.presentation.api.errors import error_response


def test_o_codigo_do_erro_vai_no_campo_error() -> None:
    resposta = error_response(409, "email_taken")

    assert resposta.status_code == 409
    assert json.loads(bytes(resposta.body)) == {"error": "email_taken"}


def test_alguns_erros_trazem_campos_a_mais() -> None:
    resposta = error_response(422, "weak_password", reasons=["too_short"])

    assert json.loads(bytes(resposta.body)) == {
        "error": "weak_password",
        "reasons": ["too_short"],
    }


def test_leva_os_cabecalhos_pedidos() -> None:
    resposta = error_response(
        401, "invalid_credentials", headers={"WWW-Authenticate": "Bearer"}
    )

    assert resposta.headers["www-authenticate"] == "Bearer"
    assert json.loads(bytes(resposta.body)) == {"error": "invalid_credentials"}
