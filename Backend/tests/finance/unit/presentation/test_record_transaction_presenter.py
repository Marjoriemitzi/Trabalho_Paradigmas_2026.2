import json
from dataclasses import replace

import pytest

from app.finance.application.dtos.record_transaction import RecordedTransaction
from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.presentation.api.v1.presenters.record_transaction_presenter import (
    RecordTransactionHttpPresenter,
)

LANCADA = RecordedTransaction(
    id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
    account_id="0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
    kind="expense",
    amount_cents=1250,
    description="Supermercado",
    category="mercado",
    occurred_on="2026-11-07",
)


def test_lancamento_gravado_vira_201_com_os_dados() -> None:
    presenter = RecordTransactionHttpPresenter()

    presenter.present_recorded(LANCADA)

    resposta = presenter.response()
    assert resposta.status_code == 201
    assert json.loads(bytes(resposta.body)) == {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "account_id": "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d",
        "kind": "expense",
        "amount_cents": 1250,
        "description": "Supermercado",
        "category": "mercado",
        "occurred_on": "2026-11-07",
        "warnings": [],
    }


def test_os_avisos_saem_com_codigo_e_detalhes() -> None:
    presenter = RecordTransactionHttpPresenter()
    aviso = TransactionWarning(
        "budget_exceeded", {"category": "lazer", "limit_cents": 30000}
    )

    presenter.present_recorded(replace(LANCADA, warnings=(aviso,)))

    corpo = json.loads(bytes(presenter.response().body))
    assert corpo["warnings"] == [
        {
            "code": "budget_exceeded",
            "details": {"category": "lazer", "limit_cents": 30000},
        }
    ]


def test_dado_recusado_vira_422_no_formato_unico() -> None:
    presenter = RecordTransactionHttpPresenter()

    presenter.present_invalid("amount_cents", "not_positive")

    resposta = presenter.response()
    assert resposta.status_code == 422
    assert json.loads(bytes(resposta.body)) == {
        "error": "invalid_transaction",
        "fields": [{"field": "amount_cents", "problem": "not_positive"}],
    }


def test_sem_nenhum_resultado_e_um_erro_claro() -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        RecordTransactionHttpPresenter().response()
