import json

import pytest

from app.shared.presentation.api.errors import ApiError
from app.users.application.dtos.get_current_user import UserProfile
from app.users.presentation.api.v1.presenters.get_current_user_presenter import (
    GetCurrentUserHttpPresenter,
)

PERFIL = UserProfile(
    id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d", email="ana@acme.com", role="user"
)


def test_usuario_encontrado_vira_200_com_os_dados() -> None:
    presenter = GetCurrentUserHttpPresenter()

    presenter.present_user(PERFIL)

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert json.loads(bytes(resposta.body)) == {
        "id": "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
        "email": "ana@acme.com",
        "role": "user",
    }


def test_usuario_que_nao_existe_mais_e_um_token_invalido() -> None:
    presenter = GetCurrentUserHttpPresenter()

    with pytest.raises(ApiError) as erro:
        presenter.present_user_not_found()

    assert erro.value.status_code == 401
    assert erro.value.code == "invalid_token"
    assert erro.value.headers == {"WWW-Authenticate": 'Bearer error="invalid_token"'}


def test_sem_nenhum_resultado_e_um_erro_claro() -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        GetCurrentUserHttpPresenter().response()
