import uuid
from datetime import date

import pytest
from pydantic import BaseModel, ValidationError

from app.finance.application.dtos.create_account import AccountOutput
from app.finance.application.dtos.get_statement import (
    StatementEntry,
    StatementOutput,
    StatementTransfer,
)
from app.finance.application.dtos.list_accounts import AccountSummary
from app.finance.application.dtos.list_categories import CategoryOutput
from app.finance.application.dtos.record_transaction import RecordedTransaction
from app.finance.application.dtos.recurrences import RecurrenceOutput
from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.dtos.transfers import TransferListOutput, TransferOutput
from app.finance.presentation.api.v1.schemas.accounts import (
    AccountListResponse,
    AccountResponse,
    AccountSummaryResponse,
    CreateAccountRequest,
    RenameAccountRequest,
)
from app.finance.presentation.api.v1.schemas.categories import (
    CategoryListResponse,
    CategoryResponse,
)
from app.finance.presentation.api.v1.schemas.get_statement import (
    StatementEntryResponse,
    StatementResponse,
    StatementTransferResponse,
)
from app.finance.presentation.api.v1.schemas.record_transaction import (
    RecordedTransactionResponse,
    RecordTransactionRequest,
    TransactionWarningResponse,
    UpdateTransactionRequest,
)
from app.finance.presentation.api.v1.schemas.recurrences import (
    RecurrenceListResponse,
    RecurrenceRequest,
    RecurrenceResponse,
)
from app.finance.presentation.api.v1.schemas.transfers import (
    CreateTransferRequest,
    TransferListResponse,
    TransferResponse,
    UpdateTransferRequest,
)

DONO = uuid.uuid4()
CONTA = uuid.uuid4()
DESTINO = uuid.uuid4()
RECURSO = uuid.uuid4()


def _erros(exc: ValidationError) -> list[tuple[tuple[int | str, ...], str]]:
    return [(err["loc"], err["type"]) for err in exc.errors()]


def _base_conta() -> dict[str, object]:
    return {"name": "Carteira", "kind": "wallet"}


def _base_renomear() -> dict[str, object]:
    return {"name": "Carteira Nova"}


def _base_transacao() -> dict[str, object]:
    return {
        "account_id": str(CONTA),
        "kind": "expense",
        "amount_cents": 1250,
        "description": "Padaria",
        "occurred_on": "2026-11-07",
    }


def _base_transferencia() -> dict[str, object]:
    return {
        "from_account_id": str(CONTA),
        "to_account_id": str(DESTINO),
        "amount_cents": 5000,
        "description": "Fatura",
        "occurred_on": "2026-11-10",
    }


def _base_recorrencia() -> dict[str, object]:
    return {
        "account_id": str(CONTA),
        "kind": "expense",
        "amount_cents": 150000,
        "description": "Aluguel",
        "frequency": "monthly",
        "day": 5,
        "starts_on": "2026-11-01",
    }


@pytest.mark.parametrize(
    ("schema", "base"),
    [
        (CreateAccountRequest, _base_conta()),
        (RenameAccountRequest, _base_renomear()),
        (RecordTransactionRequest, _base_transacao()),
        (UpdateTransactionRequest, _base_transacao()),
        (CreateTransferRequest, _base_transferencia()),
        (UpdateTransferRequest, _base_transferencia()),
        (RecurrenceRequest, _base_recorrencia()),
    ],
)
def test_requests_rejeitam_campos_extras(
    schema: type[BaseModel], base: dict[str, object]
) -> None:
    with pytest.raises(ValidationError) as exc:
        schema.model_validate({**base, "owner_id": str(DONO)})

    assert _erros(exc.value) == [(("owner_id",), "extra_forbidden")]


@pytest.mark.parametrize(
    ("schema", "base"),
    [
        (RecordTransactionRequest, _base_transacao()),
        (UpdateTransactionRequest, _base_transacao()),
        (CreateTransferRequest, _base_transferencia()),
        (UpdateTransferRequest, _base_transferencia()),
        (RecurrenceRequest, _base_recorrencia()),
    ],
)
@pytest.mark.parametrize("valor", [10.5, 10.0, True, False, "1050", None])
def test_amount_cents_com_strict_int_rejeita_nao_inteiros(
    schema: type[BaseModel], base: dict[str, object], valor: object
) -> None:
    with pytest.raises(ValidationError) as exc:
        schema.model_validate({**base, "amount_cents": valor})

    locais = [loc for loc, _ in _erros(exc.value)]
    assert locais == [("amount_cents",)]


@pytest.mark.parametrize("valor", [5.0, True, False, "5", None])
def test_day_da_recorrencia_rejeita_nao_inteiros(valor: object) -> None:
    with pytest.raises(ValidationError) as exc:
        RecurrenceRequest.model_validate({**_base_recorrencia(), "day": valor})

    assert [loc for loc, _ in _erros(exc.value)] == [("day",)]


@pytest.mark.parametrize("uuid_invalido", ["nao-e-uuid", "", "1234", 123])
def test_requests_rejeitam_uuids_invalidos(uuid_invalido: object) -> None:
    for schema, base, campo in (
        (RecordTransactionRequest, _base_transacao(), "account_id"),
        (UpdateTransactionRequest, _base_transacao(), "account_id"),
        (CreateTransferRequest, _base_transferencia(), "from_account_id"),
        (CreateTransferRequest, _base_transferencia(), "to_account_id"),
        (RecurrenceRequest, _base_recorrencia(), "account_id"),
    ):
        with pytest.raises(ValidationError) as exc:
            schema.model_validate({**base, campo: uuid_invalido})
        assert [loc for loc, _ in _erros(exc.value)] == [(campo,)]


@pytest.mark.parametrize("data_invalida", ["2026-02-30", "abc", "30/11/2026", ""])
def test_requests_rejeitam_datas_iso_invalidas(data_invalida: str) -> None:
    for schema, base, campo in (
        (RecordTransactionRequest, _base_transacao(), "occurred_on"),
        (UpdateTransactionRequest, _base_transacao(), "occurred_on"),
        (CreateTransferRequest, _base_transferencia(), "occurred_on"),
        (RecurrenceRequest, _base_recorrencia(), "starts_on"),
        (RecurrenceRequest, _base_recorrencia(), "ends_on"),
    ):
        with pytest.raises(ValidationError) as exc:
            schema.model_validate({**base, campo: data_invalida})
        assert [loc for loc, _ in _erros(exc.value)] == [(campo,)]


def test_conversoes_to_input_preservam_campos() -> None:
    conta = CreateAccountRequest.model_validate(_base_conta()).to_input(DONO)
    assert (conta.owner_id, conta.name, conta.kind) == (DONO, "Carteira", "wallet")

    renomear = RenameAccountRequest.model_validate(_base_renomear()).to_input(
        DONO, CONTA
    )
    assert (renomear.owner_id, renomear.account_id, renomear.name) == (
        DONO,
        CONTA,
        "Carteira Nova",
    )

    tx = RecordTransactionRequest.model_validate(_base_transacao()).to_input(DONO)
    assert (tx.owner_id, tx.account_id, tx.amount_cents, tx.occurred_on) == (
        DONO,
        CONTA,
        1250,
        date(2026, 11, 7),
    )

    tx_upd = UpdateTransactionRequest.model_validate(_base_transacao()).to_update_input(
        DONO, RECURSO
    )
    assert (tx_upd.owner_id, tx_upd.transaction_id, tx_upd.account_id) == (
        DONO,
        RECURSO,
        CONTA,
    )

    tr = CreateTransferRequest.model_validate(_base_transferencia()).to_input(DONO)
    assert (tr.owner_id, tr.from_account_id, tr.to_account_id) == (
        DONO,
        CONTA,
        DESTINO,
    )

    tr_upd = UpdateTransferRequest.model_validate(
        _base_transferencia()
    ).to_update_input(DONO, RECURSO)
    assert (tr_upd.owner_id, tr_upd.transfer_id, tr_upd.amount_cents) == (
        DONO,
        RECURSO,
        5000,
    )

    rec = RecurrenceRequest.model_validate(_base_recorrencia()).to_input(DONO)
    assert (rec.owner_id, rec.account_id, rec.frequency, rec.day) == (
        DONO,
        CONTA,
        "monthly",
        5,
    )

    rec_upd = RecurrenceRequest.model_validate(_base_recorrencia()).to_update_input(
        DONO, RECURSO
    )
    assert (rec_upd.owner_id, rec_upd.recurrence_id, rec_upd.starts_on) == (
        DONO,
        RECURSO,
        date(2026, 11, 1),
    )


def test_mapeamentos_de_contas_e_categorias() -> None:
    conta = AccountResponse.from_output(
        AccountOutput(id=str(CONTA), name="Nubank", kind="checking")
    )
    resumo = AccountSummaryResponse.from_summary(
        AccountSummary(
            id=str(CONTA), name="Nubank", kind="checking", balance_cents=5000
        )
    )
    lista_contas = AccountListResponse(accounts=[resumo])
    categoria = CategoryResponse.from_output(
        CategoryOutput(kind="expense", name="mercado", label="Mercado")
    )
    lista_categorias = CategoryListResponse(categories=[categoria])

    assert conta.model_dump() == {
        "id": str(CONTA),
        "name": "Nubank",
        "kind": "checking",
    }
    assert lista_contas.model_dump() == {
        "accounts": [
            {
                "id": str(CONTA),
                "name": "Nubank",
                "kind": "checking",
                "balance_cents": 5000,
            }
        ]
    }
    assert lista_categorias.model_dump() == {
        "categories": [{"kind": "expense", "name": "mercado", "label": "Mercado"}]
    }


def test_mapeamentos_de_transacoes_e_avisos() -> None:
    aviso_dto = TransactionWarning(code="budget_near", details={"percent": 80})
    aviso = TransactionWarningResponse.from_warning(aviso_dto)
    assert aviso.model_dump() == {"code": "budget_near", "details": {"percent": 80}}

    tx_dto = RecordedTransaction(
        id=str(RECURSO),
        account_id=str(CONTA),
        kind="expense",
        amount_cents=4590,
        description="Padaria",
        category="mercado",
        occurred_on="2026-11-07",
        recurrence_id=None,
        warnings=(aviso_dto,),
    )
    tx = RecordedTransactionResponse.from_output(tx_dto)

    assert tx.model_dump() == {
        "id": str(RECURSO),
        "account_id": str(CONTA),
        "kind": "expense",
        "amount_cents": 4590,
        "description": "Padaria",
        "category": "mercado",
        "occurred_on": "2026-11-07",
        "recurrence_id": None,
        "warnings": [{"code": "budget_near", "details": {"percent": 80}}],
    }


def test_mapeamentos_de_extrato_com_aliases_from_e_to() -> None:
    entry_dto = StatementEntry(
        id=str(RECURSO),
        account_id=str(CONTA),
        kind="income",
        amount_cents=100000,
        description="Salário",
        category="salario",
        occurred_on="2026-11-05",
        recurrence_id=None,
    )
    transfer_dto = StatementTransfer(
        id=str(DESTINO),
        from_account_id=str(CONTA),
        to_account_id=str(DESTINO),
        amount_cents=25000,
        description="Reserva",
        occurred_on="2026-11-10",
    )
    statement_dto = StatementOutput(
        start="2026-11-01",
        end="2026-11-30",
        account_id=str(CONTA),
        opening_balance_cents=10000,
        income_cents=100000,
        expense_cents=0,
        closing_balance_cents=85000,
        transactions=(entry_dto,),
        transfers_in_cents=0,
        transfers_out_cents=25000,
        transfers=(transfer_dto,),
    )

    assert StatementEntryResponse.from_entry(entry_dto).id == str(RECURSO)
    assert StatementTransferResponse.from_transfer(transfer_dto).id == str(DESTINO)

    serializado = StatementResponse.from_output(statement_dto).model_dump(by_alias=True)
    assert serializado["from"] == "2026-11-01"
    assert serializado["to"] == "2026-11-30"
    assert "start" not in serializado
    assert "end" not in serializado
    assert serializado["closing_balance_cents"] == 85000
    assert len(serializado["transactions"]) == 1
    assert len(serializado["transfers"]) == 1


def test_mapeamentos_de_transferencias_e_recorrencias() -> None:
    transfer_dto = TransferOutput(
        id=str(RECURSO),
        from_account_id=str(CONTA),
        to_account_id=str(DESTINO),
        amount_cents=15000,
        description="Fatura",
        occurred_on="2026-11-10",
    )
    transfer = TransferResponse.from_output(transfer_dto)
    assert transfer.model_dump()["amount_cents"] == 15000

    lista_tr = TransferListResponse.from_output(
        TransferListOutput(
            start="2026-11-01", end="2026-11-30", transfers=[transfer_dto]
        )
    ).model_dump(by_alias=True)
    assert lista_tr["from"] == "2026-11-01"
    assert lista_tr["to"] == "2026-11-30"
    assert "start" not in lista_tr
    assert "end" not in lista_tr

    rec_dto = RecurrenceOutput(
        id=str(RECURSO),
        account_id=str(CONTA),
        kind="expense",
        amount_cents=150000,
        description="Aluguel",
        category="moradia",
        frequency="monthly",
        day=5,
        starts_on="2026-11-01",
        ends_on=None,
        next_occurrence_on="2026-12-05",
        last_run_on=None,
    )
    rec = RecurrenceResponse.from_output(rec_dto)
    lista_rec = RecurrenceListResponse(recurrences=[rec])
    assert (
        lista_rec.model_dump()["recurrences"][0]["next_occurrence_on"] == "2026-12-05"
    )
