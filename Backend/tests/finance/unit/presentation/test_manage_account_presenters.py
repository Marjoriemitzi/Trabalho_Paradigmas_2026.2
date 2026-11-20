import json

import pytest

from app.finance.application.dtos.create_account import AccountOutput
from app.finance.presentation.api.v1.presenters.delete_account_presenter import (
    DeleteAccountHttpPresenter,
)
from app.finance.presentation.api.v1.presenters.rename_account_presenter import (
    RenameAccountHttpPresenter,
)

CONTA = AccountOutput(
    id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d", name="Conta do banco", kind="checking"
)


def test_renomear_vira_200_com_a_conta() -> None:
    presenter = RenameAccountHttpPresenter()

    presenter.present_renamed(CONTA)

    assert presenter.response().status_code == 200
    assert json.loads(bytes(presenter.response().body)) == {
        "id": "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
        "name": "Conta do banco",
        "kind": "checking",
    }


def test_nome_recusado_vira_422_com_o_campo() -> None:
    presenter = RenameAccountHttpPresenter()

    presenter.present_invalid("name", "blank")

    assert presenter.response().status_code == 422
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "invalid_account",
        "fields": [{"field": "name", "problem": "blank"}],
    }


def test_nome_repetido_vira_409() -> None:
    presenter = RenameAccountHttpPresenter()

    presenter.present_name_taken("Nubank")

    assert presenter.response().status_code == 409
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "account_name_taken"
    }


def test_renomear_conta_inexistente_vira_404() -> None:
    presenter = RenameAccountHttpPresenter()

    presenter.present_not_found()

    assert presenter.response().status_code == 404
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "account_not_found"
    }


def test_apagar_vira_204_sem_corpo() -> None:
    presenter = DeleteAccountHttpPresenter()

    presenter.present_deleted()

    assert presenter.response().status_code == 204
    assert bytes(presenter.response().body) == b""


def test_apagar_conta_em_uso_vira_409() -> None:
    presenter = DeleteAccountHttpPresenter()

    presenter.present_in_use()

    assert presenter.response().status_code == 409
    assert json.loads(bytes(presenter.response().body)) == {"error": "account_in_use"}


def test_apagar_conta_inexistente_vira_404() -> None:
    presenter = DeleteAccountHttpPresenter()

    presenter.present_not_found()

    assert presenter.response().status_code == 404


@pytest.mark.parametrize(
    "presenter", [RenameAccountHttpPresenter(), DeleteAccountHttpPresenter()]
)
def test_sem_resultado_apresentado_e_erro_de_programacao(
    presenter: RenameAccountHttpPresenter | DeleteAccountHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError):
        presenter.response()
