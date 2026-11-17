import json

import pytest

from app.finance.application.dtos.create_account import AccountOutput
from app.finance.application.dtos.list_accounts import AccountSummary
from app.finance.presentation.api.v1.presenters.create_account_presenter import (
    CreateAccountHttpPresenter,
)
from app.finance.presentation.api.v1.presenters.list_accounts_presenter import (
    ListAccountsHttpPresenter,
)

NUBANK = AccountOutput(
    id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d", name="Nubank", kind="checking"
)


def test_conta_aberta_vira_201() -> None:
    presenter = CreateAccountHttpPresenter()

    presenter.present_created(NUBANK)

    resposta = presenter.response()
    assert resposta.status_code == 201
    assert json.loads(bytes(resposta.body)) == {
        "id": "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
        "name": "Nubank",
        "kind": "checking",
    }


def test_nome_repetido_vira_409() -> None:
    presenter = CreateAccountHttpPresenter()

    presenter.present_name_taken("Nubank")

    resposta = presenter.response()
    assert resposta.status_code == 409
    assert json.loads(bytes(resposta.body)) == {"error": "account_name_taken"}


def test_dado_recusado_vira_422_no_formato_unico() -> None:
    presenter = CreateAccountHttpPresenter()

    presenter.present_invalid("kind", "unknown")

    resposta = presenter.response()
    assert resposta.status_code == 422
    assert json.loads(bytes(resposta.body)) == {
        "error": "invalid_account",
        "fields": [{"field": "kind", "problem": "unknown"}],
    }


def test_lista_de_contas_vira_200_com_os_saldos() -> None:
    presenter = ListAccountsHttpPresenter()

    presenter.present_accounts(
        (
            AccountSummary(
                id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
                name="Nubank",
                kind="checking",
                balance_cents=515410,
            ),
        )
    )

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert json.loads(bytes(resposta.body)) == {
        "accounts": [
            {
                "id": "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
                "name": "Nubank",
                "kind": "checking",
                "balance_cents": 515410,
            }
        ]
    }
    assert resposta.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "presenter",
    [CreateAccountHttpPresenter(), ListAccountsHttpPresenter()],
    ids=["abrir", "listar"],
)
def test_sem_nenhum_resultado_e_um_erro_claro(
    presenter: CreateAccountHttpPresenter | ListAccountsHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        presenter.response()
