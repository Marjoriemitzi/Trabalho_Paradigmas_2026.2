import json

from app.users.presentation.api.v1.presenters.authenticate_user_presenter import (
    AuthenticateUserHttpPresenter,
)
from app.users.presentation.api.v1.presenters.register_user_presenter import (
    RegisterUserHttpPresenter,
)


def test_login_bloqueado_vira_429_com_retry_after() -> None:
    presenter = AuthenticateUserHttpPresenter()

    presenter.present_too_many_attempts(742)

    resposta = presenter.response()
    assert resposta.status_code == 429
    assert resposta.headers["retry-after"] == "742"
    assert json.loads(bytes(resposta.body)) == {"error": "too_many_attempts"}


def test_cadastro_bloqueado_vira_429_com_retry_after() -> None:
    presenter = RegisterUserHttpPresenter()

    presenter.present_too_many_attempts(3000)

    resposta = presenter.response()
    assert resposta.status_code == 429
    assert resposta.headers["retry-after"] == "3000"
    assert json.loads(bytes(resposta.body)) == {"error": "too_many_attempts"}
