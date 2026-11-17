import json

import pytest

from app.finance.application.dtos.get_statement import (
    StatementEntry,
    StatementOutput,
    StatementTransfer,
)
from app.finance.presentation.api.v1.presenters.get_statement_presenter import (
    GetStatementHttpPresenter,
)

CONTA = "0b8f6c1e-4d4a-4a8e-9a57-6d1f1e2b3c4d"
CORRENTE = "5f0c2a8e-1b7d-4c3e-9f6a-2d8b4e1c7a90"
EXTRATO = StatementOutput(
    start="2026-11-01",
    end="2026-11-30",
    account_id=CONTA,
    opening_balance_cents=100000,
    income_cents=520000,
    expense_cents=4590,
    closing_balance_cents=615410,
    transactions=(
        StatementEntry(
            id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
            account_id=CONTA,
            kind="expense",
            amount_cents=4590,
            description="Padaria",
            category="mercado",
            occurred_on="2026-11-07",
        ),
    ),
    transfers_in_cents=150000,
    transfers_out_cents=0,
    transfers=(
        StatementTransfer(
            id="9a1b2c3d-4e5f-4a6b-8c7d-0e1f2a3b4c5d",
            from_account_id=CORRENTE,
            to_account_id=CONTA,
            amount_cents=150000,
            description="Pagamento da fatura",
            occurred_on="2026-11-10",
        ),
    ),
)


def test_extrato_vira_200_com_from_e_to_como_no_pedido() -> None:
    presenter = GetStatementHttpPresenter()

    presenter.present_statement(EXTRATO)

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert json.loads(bytes(resposta.body)) == {
        "from": "2026-11-01",
        "to": "2026-11-30",
        "account_id": CONTA,
        "opening_balance_cents": 100000,
        "income_cents": 520000,
        "expense_cents": 4590,
        "closing_balance_cents": 615410,
        "transactions": [
            {
                "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "account_id": CONTA,
                "kind": "expense",
                "amount_cents": 4590,
                "description": "Padaria",
                "category": "mercado",
                "occurred_on": "2026-11-07",
            }
        ],
        "transfers_in_cents": 150000,
        "transfers_out_cents": 0,
        "transfers": [
            {
                "id": "9a1b2c3d-4e5f-4a6b-8c7d-0e1f2a3b4c5d",
                "from_account_id": CORRENTE,
                "to_account_id": CONTA,
                "amount_cents": 150000,
                "description": "Pagamento da fatura",
                "occurred_on": "2026-11-10",
            }
        ],
    }


def test_extrato_nao_fica_guardado_em_cache() -> None:
    presenter = GetStatementHttpPresenter()

    presenter.present_statement(EXTRATO)

    assert presenter.response().headers["cache-control"] == "no-store"


def test_periodo_recusado_vira_422_no_formato_unico() -> None:
    presenter = GetStatementHttpPresenter()

    presenter.present_invalid("to", "end_before_start")

    resposta = presenter.response()
    assert resposta.status_code == 422
    assert json.loads(bytes(resposta.body)) == {
        "error": "invalid_period",
        "fields": [{"field": "to", "problem": "end_before_start"}],
    }


def test_conta_que_nao_e_de_quem_pediu_vira_404() -> None:
    presenter = GetStatementHttpPresenter()

    presenter.present_account_not_found()

    resposta = presenter.response()
    assert resposta.status_code == 404
    assert json.loads(bytes(resposta.body)) == {"error": "account_not_found"}


def test_sem_nenhum_resultado_e_um_erro_claro() -> None:
    with pytest.raises(RuntimeError, match="sem apresentar"):
        GetStatementHttpPresenter().response()
