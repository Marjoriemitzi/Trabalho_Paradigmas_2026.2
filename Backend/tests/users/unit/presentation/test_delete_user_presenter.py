import json

import pytest

from app.shared.presentation.api.errors import ApiError
from app.users.presentation.api.v1.presenters.delete_user_presenter import (
    DeleteUserHttpPresenter,
)


def test_apagar_vira_204_sem_corpo() -> None:
    presenter = DeleteUserHttpPresenter()

    presenter.present_deleted()

    assert presenter.response().status_code == 204
    assert bytes(presenter.response().body) == b""


def test_senha_errada_vira_422() -> None:
    presenter = DeleteUserHttpPresenter()

    presenter.present_invalid_current_password()

    assert presenter.response().status_code == 422
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "invalid_current_password"
    }


def test_usuario_que_nao_existe_mais_vira_401_invalid_token() -> None:
    with pytest.raises(ApiError) as erro:
        DeleteUserHttpPresenter().present_user_not_found()

    assert erro.value.status_code == 401
    assert erro.value.code == "invalid_token"


def test_sem_resultado_apresentado_e_erro_de_programacao() -> None:
    with pytest.raises(RuntimeError):
        DeleteUserHttpPresenter().response()
