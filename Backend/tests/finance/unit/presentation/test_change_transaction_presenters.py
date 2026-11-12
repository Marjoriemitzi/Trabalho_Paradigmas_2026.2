import json

import pytest

from app.finance.application.dtos.record_transaction import RecordedTransaction
from app.finance.presentation.api.v1.presenters.change_transaction_presenters import (
    DeleteTransactionHttpPresenter,
    UpdateTransactionHttpPresenter,
)

CORRIGIDA = RecordedTransaction(
    id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
    account_id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
    kind="expense",
    amount_cents=4950,
    description="Padaria São Jorge",
    category="mercado",
    occurred_on="2026-11-08",
)


def test_correcao_vira_200_com_a_transacao_como_ficou() -> None:
    presenter = UpdateTransactionHttpPresenter()

    presenter.present_updated(CORRIGIDA)

    resposta = presenter.response()
    assert resposta.status_code == 200
    corpo = json.loads(bytes(resposta.body))
    assert corpo["amount_cents"] == 4950
    assert corpo["warnings"] == []


def test_correcao_recusada_vira_422_no_formato_unico() -> None:
    presenter = UpdateTransactionHttpPresenter()

    presenter.present_invalid("category", "not_found")

    resposta = presenter.response()
    assert resposta.status_code == 422
    assert json.loads(bytes(resposta.body)) == {
        "error": "invalid_transaction",
        "fields": [{"field": "category", "problem": "not_found"}],
    }


def test_apagada_vira_204_sem_corpo() -> None:
    presenter = DeleteTransactionHttpPresenter()

    presenter.present_deleted()

    resposta = presenter.response()
    assert resposta.status_code == 204
    assert resposta.body == b""


@pytest.mark.parametrize(
    "presenter",
    [UpdateTransactionHttpPresenter(), DeleteTransactionHttpPresenter()],
    ids=["corrigir", "apagar"],
)
def test_transacao_que_nao_e_de_quem_pediu_vira_404(
    presenter: UpdateTransactionHttpPresenter | DeleteTransactionHttpPresenter,
) -> None:
    presenter.present_not_found()

    resposta = presenter.response()
    assert resposta.status_code == 404
    assert json.loads(bytes(resposta.body)) == {"error": "transaction_not_found"}


@pytest.mark.parametrize(
    "presenter",
    [UpdateTransactionHttpPresenter(), DeleteTransactionHttpPresenter()],
    ids=["corrigir", "apagar"],
)
def test_sem_nenhum_resultado_e_um_erro_claro(
    presenter: UpdateTransactionHttpPresenter | DeleteTransactionHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        presenter.response()
