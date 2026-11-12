import json

import pytest

from app.finance.application.dtos.transfers import TransferOutput
from app.finance.presentation.api.v1.presenters.transfer_presenters import (
    CreateTransferHttpPresenter,
    DeleteTransferHttpPresenter,
)

FATURA = TransferOutput(
    id="9a1b2c3d-4e5f-4a6b-8c7d-0e1f2a3b4c5d",
    from_account_id="5f0c2a8e-1b7d-4c3e-9f6a-2d8b4e1c7a90",
    to_account_id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
    amount_cents=150000,
    description="Pagamento da fatura",
    occurred_on="2026-11-10",
)


def test_transferencia_criada_vira_201() -> None:
    presenter = CreateTransferHttpPresenter()

    presenter.present_created(FATURA)

    resposta = presenter.response()
    assert resposta.status_code == 201
    assert json.loads(bytes(resposta.body)) == {
        "id": "9a1b2c3d-4e5f-4a6b-8c7d-0e1f2a3b4c5d",
        "from_account_id": "5f0c2a8e-1b7d-4c3e-9f6a-2d8b4e1c7a90",
        "to_account_id": "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
        "amount_cents": 150000,
        "description": "Pagamento da fatura",
        "occurred_on": "2026-11-10",
    }


def test_dado_recusado_vira_422_no_formato_unico() -> None:
    presenter = CreateTransferHttpPresenter()

    presenter.present_invalid("to_account_id", "same_account")

    resposta = presenter.response()
    assert resposta.status_code == 422
    assert json.loads(bytes(resposta.body)) == {
        "error": "invalid_transfer",
        "fields": [{"field": "to_account_id", "problem": "same_account"}],
    }


def test_apagada_vira_204_e_nao_encontrada_vira_404() -> None:
    apagada, nao_encontrada = (
        DeleteTransferHttpPresenter(),
        DeleteTransferHttpPresenter(),
    )

    apagada.present_deleted()
    nao_encontrada.present_not_found()

    assert apagada.response().status_code == 204
    assert nao_encontrada.response().status_code == 404
    assert json.loads(bytes(nao_encontrada.response().body)) == {
        "error": "transfer_not_found"
    }


@pytest.mark.parametrize(
    "presenter",
    [CreateTransferHttpPresenter(), DeleteTransferHttpPresenter()],
    ids=["criar", "apagar"],
)
def test_sem_nenhum_resultado_e_um_erro_claro(
    presenter: CreateTransferHttpPresenter | DeleteTransferHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        presenter.response()
