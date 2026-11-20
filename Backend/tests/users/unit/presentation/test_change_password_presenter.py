import json

import pytest

from app.shared.presentation.api.errors import ApiError
from app.users.presentation.api.v1.presenters.change_password_presenter import (
    ChangePasswordHttpPresenter,
)


def corpo(presenter: ChangePasswordHttpPresenter) -> object:
    return json.loads(bytes(presenter.response().body))


def test_troca_vira_204_sem_corpo() -> None:
    presenter = ChangePasswordHttpPresenter()

    presenter.present_changed()

    assert presenter.response().status_code == 204
    assert bytes(presenter.response().body) == b""


def test_senha_atual_errada_vira_422() -> None:
    presenter = ChangePasswordHttpPresenter()

    presenter.present_invalid_current_password()

    assert presenter.response().status_code == 422
    assert corpo(presenter) == {"error": "invalid_current_password"}


def test_senha_nova_fraca_vira_422_com_reasons() -> None:
    presenter = ChangePasswordHttpPresenter()

    presenter.present_weak_password(["too_short", "no_symbol"])

    assert presenter.response().status_code == 422
    assert corpo(presenter) == {
        "error": "weak_password",
        "reasons": ["too_short", "no_symbol"],
    }


def test_usuario_que_nao_existe_mais_vira_401_invalid_token() -> None:
    presenter = ChangePasswordHttpPresenter()

    with pytest.raises(ApiError) as erro:
        presenter.present_user_not_found()

    assert erro.value.status_code == 401
    assert erro.value.code == "invalid_token"


def test_sem_resultado_apresentado_e_erro_de_programacao() -> None:
    with pytest.raises(RuntimeError):
        ChangePasswordHttpPresenter().response()
