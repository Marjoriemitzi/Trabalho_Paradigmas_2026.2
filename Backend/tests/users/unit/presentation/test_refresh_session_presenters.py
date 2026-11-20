import json

import pytest

from app.users.application.ports.token_issuer import AccessToken
from app.users.application.session import Session
from app.users.presentation.api.v1.presenters.logout_presenter import (
    LogoutHttpPresenter,
)
from app.users.presentation.api.v1.presenters.refresh_session_presenter import (
    RefreshSessionHttpPresenter,
)
from app.users.presentation.api.v1.schemas.refresh_session import (
    RefreshSessionRequest,
)

SESSAO = Session(
    access_token=AccessToken("abc.def.ghi", expires_in=900),
    refresh_token="Qm9r",
    refresh_expires_in=2592000,
)


def test_renovacao_vira_200_com_o_par_novo_e_no_store() -> None:
    presenter = RefreshSessionHttpPresenter()

    presenter.present_refreshed(SESSAO)

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert json.loads(bytes(resposta.body)) == {
        "access_token": "abc.def.ghi",
        "token_type": "bearer",
        "expires_in": 900,
        "refresh_token": "Qm9r",
        "refresh_expires_in": 2592000,
    }


def test_refresh_token_invalido_vira_401() -> None:
    presenter = RefreshSessionHttpPresenter()

    presenter.present_invalid_refresh_token()

    assert presenter.response().status_code == 401
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "invalid_refresh_token"
    }


def test_logout_vira_204_sem_corpo() -> None:
    presenter = LogoutHttpPresenter()

    presenter.present_logged_out()

    assert presenter.response().status_code == 204
    assert bytes(presenter.response().body) == b""


@pytest.mark.parametrize(
    "presenter", [RefreshSessionHttpPresenter(), LogoutHttpPresenter()]
)
def test_sem_resultado_apresentado_e_erro_de_programacao(
    presenter: RefreshSessionHttpPresenter | LogoutHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError):
        presenter.response()


def test_o_refresh_token_do_pedido_nao_aparece_em_logs() -> None:
    pedido = RefreshSessionRequest(refresh_token="segredo-do-refresh")

    assert "segredo" not in repr(pedido)
    assert "segredo" not in repr(pedido.to_refresh_input())
    assert "segredo" not in repr(pedido.to_logout_input())
    assert "segredo" not in repr(SESSAO)
