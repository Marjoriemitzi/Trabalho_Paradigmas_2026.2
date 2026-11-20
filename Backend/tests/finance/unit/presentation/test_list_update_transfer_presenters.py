import json

import pytest

from app.finance.application.dtos.transfers import TransferListOutput, TransferOutput
from app.finance.presentation.api.v1.presenters.transfer_presenters import (
    ListTransfersHttpPresenter,
    UpdateTransferHttpPresenter,
)

TRANSFERENCIA = TransferOutput(
    id="7e4f0000-0000-4000-8000-000000000001",
    from_account_id="a1b20000-0000-4000-8000-000000000002",
    to_account_id="c3d40000-0000-4000-8000-000000000003",
    amount_cents=50000,
    description="Para a carteira",
    occurred_on="2026-11-05",
)


def test_listagem_vira_200_com_from_to_e_no_store() -> None:
    presenter = ListTransfersHttpPresenter()

    presenter.present_listed(
        TransferListOutput(
            start="2026-11-01", end="2026-11-30", transfers=[TRANSFERENCIA]
        )
    )

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert json.loads(bytes(resposta.body)) == {
        "from": "2026-11-01",
        "to": "2026-11-30",
        "transfers": [
            {
                "id": TRANSFERENCIA.id,
                "from_account_id": TRANSFERENCIA.from_account_id,
                "to_account_id": TRANSFERENCIA.to_account_id,
                "amount_cents": 50000,
                "description": "Para a carteira",
                "occurred_on": "2026-11-05",
            }
        ],
    }


def test_periodo_recusado_vira_422_invalid_period() -> None:
    presenter = ListTransfersHttpPresenter()

    presenter.present_invalid("to", "too_long")

    assert presenter.response().status_code == 422
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "invalid_period",
        "fields": [{"field": "to", "problem": "too_long"}],
    }


def test_correcao_vira_200_com_no_store() -> None:
    presenter = UpdateTransferHttpPresenter()

    presenter.present_updated(TRANSFERENCIA)

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert json.loads(bytes(resposta.body))["amount_cents"] == 50000


def test_correcao_recusada_vira_422_invalid_transfer() -> None:
    presenter = UpdateTransferHttpPresenter()

    presenter.present_invalid("to_account_id", "same_account")

    assert presenter.response().status_code == 422
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "invalid_transfer",
        "fields": [{"field": "to_account_id", "problem": "same_account"}],
    }


def test_correcao_de_transferencia_inexistente_vira_404() -> None:
    presenter = UpdateTransferHttpPresenter()

    presenter.present_not_found()

    assert presenter.response().status_code == 404
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "transfer_not_found"
    }


@pytest.mark.parametrize(
    "presenter", [ListTransfersHttpPresenter(), UpdateTransferHttpPresenter()]
)
def test_sem_resultado_apresentado_e_erro_de_programacao(
    presenter: ListTransfersHttpPresenter | UpdateTransferHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError):
        presenter.response()
