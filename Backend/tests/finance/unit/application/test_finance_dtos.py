import uuid
from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.finance.application.dtos.change_transaction import (
    DeleteTransactionInput,
    UpdateTransactionInput,
)
from app.finance.application.dtos.create_account import (
    AccountOutput,
    CreateAccountInput,
)
from app.finance.application.dtos.delete_account import DeleteAccountInput
from app.finance.application.dtos.get_statement import (
    GetStatementInput,
    StatementEntry,
    StatementOutput,
    StatementTransfer,
)
from app.finance.application.dtos.list_accounts import AccountSummary, ListAccountsInput
from app.finance.application.dtos.list_categories import CategoryOutput
from app.finance.application.dtos.record_transaction import (
    RecordedTransaction,
    RecordTransactionInput,
)
from app.finance.application.dtos.recurrences import (
    CreateRecurrenceInput,
    DeleteRecurrenceInput,
    ListRecurrencesInput,
    RecurrenceOutput,
    UpdateRecurrenceInput,
)
from app.finance.application.dtos.rename_account import RenameAccountInput
from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.dtos.transfers import (
    CreateTransferInput,
    DeleteTransferInput,
    ListTransfersInput,
    TransferListOutput,
    TransferOutput,
    UpdateTransferInput,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_entry import CategoryEntry
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.recurrence_id import RecurrenceId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.statement import Statement
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.domain.value_objects.transfer_flows import TransferFlows

DONO = OwnerId(uuid.uuid4())
ORIGEM = Account.open(DONO, AccountName("Corrente"), AccountKind.CHECKING)
DESTINO = Account.open(DONO, AccountName("Carteira"), AccountKind.WALLET)


def _transacao(recorrencia: RecurrenceId | None = None) -> Transaction:
    return Transaction.record(
        owner=DONO,
        account=ORIGEM.id,
        kind=TransactionKind.EXPENSE,
        amount=Money(4590),
        description=Description("Padaria"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
        recurrence=recorrencia,
    )


def _transferencia() -> Transfer:
    return Transfer.record(
        owner=DONO,
        source=ORIGEM.id,
        destination=DESTINO.id,
        amount=Money(15000),
        description=Description("Para carteira"),
        occurred_on=date(2026, 11, 10),
    )


def test_account_output_e_account_summary_from_account() -> None:
    saida = AccountOutput.from_account(ORIGEM)
    resumo = AccountSummary.from_account(
        ORIGEM,
        Totals(income_cents=100000, expense_cents=25000),
        TransferFlows(incoming_cents=5000, outgoing_cents=15000),
    )

    assert saida == AccountOutput(
        id=str(ORIGEM.id.value), name="Corrente", kind="checking"
    )
    assert resumo == AccountSummary(
        id=str(ORIGEM.id.value),
        name="Corrente",
        kind="checking",
        balance_cents=65000,
    )


def test_category_output_from_entry() -> None:
    entrada = CategoryEntry(
        kind=TransactionKind.EXPENSE, category=Category("mercado"), label="Mercado"
    )

    assert CategoryOutput.from_entry(entrada) == CategoryOutput(
        kind="expense", name="mercado", label="Mercado"
    )


def test_recorded_transaction_from_transaction() -> None:
    recorrencia = RecurrenceId.new()
    aviso = TransactionWarning(code="aviso", details={"k": 1})
    tx = _transacao(recorrencia=recorrencia)

    dto = RecordedTransaction.from_transaction(tx, warnings=(aviso,))

    assert dto == RecordedTransaction(
        id=str(tx.id.value),
        account_id=str(ORIGEM.id.value),
        kind="expense",
        amount_cents=4590,
        description="Padaria",
        category="mercado",
        occurred_on="2026-11-07",
        recurrence_id=str(recorrencia.value),
        warnings=(aviso,),
    )
    assert RecordedTransaction.from_transaction(_transacao()).recurrence_id is None


def test_statement_dtos_from_domain_sem_conta_e_com_conta() -> None:
    periodo = Period(date(2026, 11, 1), date(2026, 11, 30))
    tx = _transacao()
    tr = _transferencia()

    geral = StatementOutput.from_statement(
        Statement(
            period=periodo,
            opening_balance_cents=50000,
            transactions=(tx,),
            account=None,
        )
    )
    assert geral.account_id is None
    assert geral.start == "2026-11-01"
    assert geral.end == "2026-11-30"
    assert geral.closing_balance_cents == 50000 - 4590
    assert geral.transfers == ()
    assert geral.transactions == (StatementEntry.from_transaction(tx),)

    por_conta = StatementOutput.from_statement(
        Statement(
            period=periodo,
            opening_balance_cents=50000,
            transactions=(tx,),
            transfers=(tr,),
            account=AccountId(ORIGEM.id.value),
        )
    )
    assert por_conta.account_id == str(ORIGEM.id.value)
    assert por_conta.transfers_in_cents == 0
    assert por_conta.transfers_out_cents == 15000
    assert por_conta.closing_balance_cents == 50000 - 4590 - 15000
    assert por_conta.transfers == (StatementTransfer.from_transfer(tr),)


def test_transfer_output_e_recurrence_output_from_entities() -> None:
    tr = _transferencia()
    assert TransferOutput.from_transfer(tr) == TransferOutput(
        id=str(tr.id.value),
        from_account_id=str(ORIGEM.id.value),
        to_account_id=str(DESTINO.id.value),
        amount_cents=15000,
        description="Para carteira",
        occurred_on="2026-11-10",
    )

    rec = Recurrence.create(
        owner=DONO,
        account=ORIGEM.id,
        kind=TransactionKind.EXPENSE,
        amount=Money(150000),
        description=Description("Aluguel"),
        category=None,
        schedule=Schedule(Frequency.MONTHLY, 5),
        window=ActiveRange(date(2026, 11, 1), date(2027, 11, 1)),
    )
    rec.mark_run(date(2026, 11, 5))
    assert RecurrenceOutput.from_recurrence(rec, date(2026, 12, 5)) == RecurrenceOutput(
        id=str(rec.id.value),
        account_id=str(ORIGEM.id.value),
        kind="expense",
        amount_cents=150000,
        description="Aluguel",
        category=None,
        frequency="monthly",
        day=5,
        starts_on="2026-11-01",
        ends_on="2027-11-01",
        next_occurrence_on="2026-12-05",
        last_run_on="2026-11-05",
    )


def _todos_os_dtos() -> list[tuple[object, str, object]]:
    uid = uuid.uuid4()
    hoje = date(2026, 11, 7)
    return [
        (CreateAccountInput(uid, "Carteira", "wallet"), "name", "Outro"),
        (AccountOutput("1", "Carteira", "wallet"), "name", "Outro"),
        (RenameAccountInput(uid, uid, "Nova"), "name", "Outro"),
        (DeleteAccountInput(uid, uid), "owner_id", uuid.uuid4()),
        (ListAccountsInput(uid), "owner_id", uuid.uuid4()),
        (AccountSummary("1", "Carteira", "wallet", 0), "balance_cents", 10),
        (CategoryOutput("expense", "mercado", "Mercado"), "label", "Outro"),
        (
            RecordTransactionInput(uid, uid, "expense", 100, "Desc", hoje),
            "amount_cents",
            200,
        ),
        (
            RecordedTransaction(
                "1", "2", "expense", 100, "Desc", "outros", "2026-11-07"
            ),
            "amount_cents",
            200,
        ),
        (TransactionWarning("code", {"a": 1}), "code", "outro"),
        (
            UpdateTransactionInput(uid, uid, uid, "expense", 100, "Desc", hoje),
            "amount_cents",
            200,
        ),
        (DeleteTransactionInput(uid, uid), "owner_id", uuid.uuid4()),
        (GetStatementInput(uid, hoje, hoje), "start", date(2026, 11, 8)),
        (
            StatementEntry(
                "1", "2", "expense", 100, "Desc", "outros", "2026-11-07", None
            ),
            "amount_cents",
            200,
        ),
        (
            StatementTransfer("1", "2", "3", 100, "Desc", "2026-11-07"),
            "amount_cents",
            200,
        ),
        (
            StatementOutput("2026-11-01", "2026-11-30", None, 0, 0, 0, 0, ()),
            "opening_balance_cents",
            1,
        ),
        (CreateTransferInput(uid, uid, uid, 100, "Desc", hoje), "amount_cents", 200),
        (
            UpdateTransferInput(uid, uid, uid, uid, 100, "Desc", hoje),
            "amount_cents",
            200,
        ),
        (DeleteTransferInput(uid, uid), "owner_id", uuid.uuid4()),
        (ListTransfersInput(uid, hoje, hoje), "start", date(2026, 11, 8)),
        (TransferOutput("1", "2", "3", 100, "Desc", "2026-11-07"), "amount_cents", 200),
        (TransferListOutput("2026-11-01", "2026-11-30", []), "start", "2026-12-01"),
        (
            CreateRecurrenceInput(
                uid, uid, "expense", 100, "Desc", None, "monthly", 5, hoje, None
            ),
            "day",
            10,
        ),
        (
            UpdateRecurrenceInput(
                uid, uid, uid, "expense", 100, "Desc", None, "monthly", 5, hoje, None
            ),
            "day",
            10,
        ),
        (DeleteRecurrenceInput(uid, uid), "owner_id", uuid.uuid4()),
        (ListRecurrencesInput(uid), "owner_id", uuid.uuid4()),
        (
            RecurrenceOutput(
                "1",
                "2",
                "expense",
                100,
                "Desc",
                None,
                "monthly",
                5,
                "2026-11-01",
                None,
                None,
                None,
            ),
            "day",
            10,
        ),
    ]


@pytest.mark.parametrize(("dto", "campo", "novo_valor"), _todos_os_dtos())
def test_dtos_de_finance_sao_imutaveis(
    dto: object, campo: str, novo_valor: object
) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(dto, campo, novo_valor)
