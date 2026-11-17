import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.fields import InvalidFieldError, read_field
from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.services.categorizer import Categorizer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind


class TransactionFieldsInput(Protocol):
    @property
    def account_id(self) -> uuid.UUID: ...
    @property
    def kind(self) -> str: ...
    @property
    def amount_cents(self) -> int: ...
    @property
    def description(self) -> str: ...
    @property
    def occurred_on(self) -> date: ...
    @property
    def category(self) -> str | None: ...


@dataclass(frozen=True, slots=True)
class TransactionFields:
    account: AccountId
    kind: TransactionKind
    amount: Money
    description: Description
    category: Category
    occurred_on: date
    category_from_request: bool


def read_transaction_fields(
    data: TransactionFieldsInput, categorizer: Categorizer
) -> TransactionFields:
    kind = read_field("kind", TransactionKind.parse, data.kind)
    amount = read_field("amount_cents", Money, data.amount_cents)
    description = read_field("description", Description, data.description)
    if data.category is None:
        category = categorizer.categorize(kind, description)
    else:
        category = read_field("category", Category, data.category)
    return TransactionFields(
        account=AccountId(data.account_id),
        kind=kind,
        amount=amount,
        description=description,
        category=category,
        occurred_on=data.occurred_on,
        category_from_request=data.category is not None,
    )


async def reference_problem(
    uow: UnitOfWork, owner: OwnerId, fields: TransactionFields
) -> InvalidFieldError | None:
    if await uow.accounts.get(owner, fields.account) is None:
        return InvalidFieldError("account_id", "not_found")
    if fields.category_from_request and not await uow.categories.contains(
        fields.kind, fields.category
    ):
        return InvalidFieldError("category", "not_found")
    return None


async def run_checks(
    checks: tuple[TransactionCheck, ...], transaction: Transaction, uow: UnitOfWork
) -> tuple[TransactionWarning, ...]:
    avisos: list[TransactionWarning] = []
    for verificacao in checks:
        avisos.extend(await verificacao.check(transaction, uow))
    return tuple(avisos)
