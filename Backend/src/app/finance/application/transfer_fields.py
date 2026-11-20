import uuid
from dataclasses import dataclass
from datetime import date

from app.finance.application.fields import InvalidFieldError, read_field
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId


@dataclass(frozen=True, slots=True)
class TransferFields:
    source: AccountId
    destination: AccountId
    amount: Money
    description: Description
    occurred_on: date


def read_transfer_fields(
    from_account_id: uuid.UUID,
    to_account_id: uuid.UUID,
    amount_cents: int,
    description: str,
    occurred_on: date,
) -> TransferFields:
    amount = read_field("amount_cents", Money, amount_cents)
    texto = read_field("description", Description, description)
    if from_account_id == to_account_id:
        raise InvalidFieldError("to_account_id", "same_account")
    return TransferFields(
        source=AccountId(from_account_id),
        destination=AccountId(to_account_id),
        amount=amount,
        description=texto,
        occurred_on=occurred_on,
    )


async def reference_problem(
    uow: UnitOfWork, owner: OwnerId, fields: TransferFields
) -> InvalidFieldError | None:
    for campo, conta in (
        ("from_account_id", fields.source),
        ("to_account_id", fields.destination),
    ):
        if await uow.accounts.get(owner, conta) is None:
            return InvalidFieldError(campo, "not_found")
    return None
