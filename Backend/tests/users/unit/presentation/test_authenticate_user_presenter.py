import json

import pytest

from app.users.application.ports.token_issuer import AccessToken
from app.users.presentation.api.v1.presenters.authenticate_user_presenter import (
    AuthenticateUserHttpPresenter,
)


def test_login_vira_200_com_o_token() -> None:
    presenter = AuthenticateUserHttpPresenter()

    presenter.present_authenticated(AccessToken("abc.def.ghi", expires_in=1800))

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert json.loads(bytes(resposta.body)) == {
        "access_token": "abc.def.ghi",
        "token_type": "bearer",
        "expires_in": 1800,
    }


def test_o_token_nao_fica_guardado_em_cache() -> None:
    presenter = AuthenticateUserHttpPresenter()

    presenter.present_authenticated(AccessToken("abc.def.ghi", expires_in=1800))

    assert presenter.response().headers["cache-control"] == "no-store"


def test_credenciais_invalidas_viram_401() -> None:
    presenter = AuthenticateUserHttpPresenter()

    presenter.present_invalid_credentials()

    resposta = presenter.response()
    assert resposta.status_code == 401
    assert json.loads(bytes(resposta.body)) == {"error": "invalid_credentials"}
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_sem_nenhum_resultado_e_um_erro_claro() -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        AuthenticateUserHttpPresenter().response()
