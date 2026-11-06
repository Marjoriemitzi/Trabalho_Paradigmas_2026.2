"""Testes do presenter HTTP do cadastro: cada resultado vira um status e um corpo."""

import json

import pytest

from app.users.application.dtos.register_user import RegisteredUser
from app.users.presentation.api.v1.presenters.register_user_presenter import (
    RegisterUserHttpPresenter,
)

USUARIO = RegisteredUser(
    id="1b4e28ba-2fa1-4d3b-8e8c-123456789abc", email="ana@acme.com", role="user"
)


def corpo(presenter: RegisterUserHttpPresenter) -> object:
    return json.loads(bytes(presenter.response().body))


def test_cadastro_vira_201_com_o_usuario() -> None:
    presenter = RegisterUserHttpPresenter()

    presenter.present_registered(USUARIO)

    assert presenter.response().status_code == 201
    assert corpo(presenter) == {
        "id": "1b4e28ba-2fa1-4d3b-8e8c-123456789abc",
        "email": "ana@acme.com",
        "role": "user",
    }


def test_email_ja_usado_vira_409() -> None:
    presenter = RegisterUserHttpPresenter()

    presenter.present_email_taken("ana@acme.com")

    assert presenter.response().status_code == 409
    assert corpo(presenter) == {"error": "email_taken"}


def test_senha_fraca_vira_422_com_os_motivos() -> None:
    presenter = RegisterUserHttpPresenter()

    presenter.present_weak_password(["too_short", "no_upper"])

    assert presenter.response().status_code == 422
    assert corpo(presenter) == {
        "error": "weak_password",
        "reasons": ["too_short", "no_upper"],
    }


def test_email_invalido_vira_422() -> None:
    presenter = RegisterUserHttpPresenter()

    presenter.present_invalid_email("nao-e-email")

    assert presenter.response().status_code == 422
    assert corpo(presenter) == {"error": "invalid_email"}


def test_sem_nenhum_resultado_e_um_erro_claro() -> None:
    presenter = RegisterUserHttpPresenter()
    with pytest.raises(RuntimeError, match="sem apresentar"):
        presenter.response()
