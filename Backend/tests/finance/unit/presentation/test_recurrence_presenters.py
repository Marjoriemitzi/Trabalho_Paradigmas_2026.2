import json

import pytest

from app.finance.application.dtos.recurrences import RecurrenceOutput
from app.finance.presentation.api.v1.presenters.recurrence_presenters import (
    CreateRecurrenceHttpPresenter,
    DeleteRecurrenceHttpPresenter,
    ListRecurrencesHttpPresenter,
    UpdateRecurrenceHttpPresenter,
)

ALUGUEL = RecurrenceOutput(
    id="5b0e0000-0000-4000-8000-000000000001",
    account_id="a1b20000-0000-4000-8000-000000000002",
    kind="expense",
    amount_cents=150000,
    description="Aluguel",
    category="moradia",
    frequency="monthly",
    day=5,
    starts_on="2026-12-01",
    ends_on=None,
    next_occurrence_on="2026-12-05",
    last_run_on=None,
)
CORPO = {
    "id": ALUGUEL.id,
    "account_id": ALUGUEL.account_id,
    "kind": "expense",
    "amount_cents": 150000,
    "description": "Aluguel",
    "category": "moradia",
    "frequency": "monthly",
    "day": 5,
    "starts_on": "2026-12-01",
    "ends_on": None,
    "next_occurrence_on": "2026-12-05",
    "last_run_on": None,
}


def test_criar_vira_201_com_a_recorrencia_e_no_store() -> None:
    presenter = CreateRecurrenceHttpPresenter()

    presenter.present_created(ALUGUEL)

    resposta = presenter.response()
    assert resposta.status_code == 201
    assert resposta.headers["cache-control"] == "no-store"
    assert json.loads(bytes(resposta.body)) == CORPO


def test_criar_recusado_vira_422_com_o_campo() -> None:
    presenter = CreateRecurrenceHttpPresenter()

    presenter.present_invalid("day", "out_of_range")

    assert presenter.response().status_code == 422
    assert json.loads(bytes(presenter.response().body)) == {
        "error": "invalid_recurrence",
        "fields": [{"field": "day", "problem": "out_of_range"}],
    }


def test_corrigir_vira_200_com_no_store() -> None:
    presenter = UpdateRecurrenceHttpPresenter()

    presenter.present_updated(ALUGUEL)

    assert presenter.response().status_code == 200
    assert presenter.response().headers["cache-control"] == "no-store"


def test_corrigir_recusado_e_nao_encontrado() -> None:
    recusado, ausente = UpdateRecurrenceHttpPresenter(), UpdateRecurrenceHttpPresenter()

    recusado.present_invalid("ends_on", "end_before_start")
    ausente.present_not_found()

    assert recusado.response().status_code == 422
    assert ausente.response().status_code == 404
    assert json.loads(bytes(ausente.response().body)) == {
        "error": "recurrence_not_found"
    }


def test_apagar_vira_204_e_nao_encontrado_vira_404() -> None:
    apagada, ausente = DeleteRecurrenceHttpPresenter(), DeleteRecurrenceHttpPresenter()

    apagada.present_deleted()
    ausente.present_not_found()

    assert apagada.response().status_code == 204
    assert bytes(apagada.response().body) == b""
    assert ausente.response().status_code == 404


def test_listar_vira_200_com_a_lista_e_no_store() -> None:
    presenter = ListRecurrencesHttpPresenter()

    presenter.present_listed([ALUGUEL])

    resposta = presenter.response()
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert json.loads(bytes(resposta.body)) == {"recurrences": [CORPO]}


@pytest.mark.parametrize(
    "presenter",
    [
        CreateRecurrenceHttpPresenter(),
        UpdateRecurrenceHttpPresenter(),
        DeleteRecurrenceHttpPresenter(),
        ListRecurrencesHttpPresenter(),
    ],
)
def test_sem_resultado_apresentado_e_erro_de_programacao(
    presenter: CreateRecurrenceHttpPresenter
    | UpdateRecurrenceHttpPresenter
    | DeleteRecurrenceHttpPresenter
    | ListRecurrencesHttpPresenter,
) -> None:
    with pytest.raises(RuntimeError):
        presenter.response()
