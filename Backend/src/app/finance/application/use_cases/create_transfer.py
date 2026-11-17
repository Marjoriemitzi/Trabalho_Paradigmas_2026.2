from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.transfers import CreateTransferInput, TransferOutput
from app.finance.application.fields import InvalidFieldError, read_field
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId


class CreateTransferInputPort(Protocol):
    async def execute(self, data: CreateTransferInput) -> None: ...


class CreateTransferOutputPort(Protocol):
    def present_created(self, transfer: TransferOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...


@dataclass(frozen=True, slots=True)
class CreateTransferInteractor(CreateTransferInputPort):
    uow: UnitOfWork
    presenter: CreateTransferOutputPort

    async def execute(self, data: CreateTransferInput) -> None:
        try:
            transfer = self._build(data)
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        async with self.uow:
            for campo, conta in (
                ("from_account_id", transfer.source),
                ("to_account_id", transfer.destination),
            ):
                if await self.uow.accounts.get(transfer.owner, conta) is None:
                    self.presenter.present_invalid(campo, "not_found")
                    return
            await self.uow.transfers.add(transfer)
            await self.uow.commit()

        self.presenter.present_created(TransferOutput.from_transfer(transfer))

    def _build(self, data: CreateTransferInput) -> Transfer:
        amount = read_field("amount_cents", Money, data.amount_cents)
        description = read_field("description", Description, data.description)
        try:
            return Transfer.record(
                owner=OwnerId(data.owner_id),
                source=AccountId(data.from_account_id),
                destination=AccountId(data.to_account_id),
                amount=amount,
                description=description,
                occurred_on=data.occurred_on,
            )
        except InvalidValueError as error:
            raise InvalidFieldError("to_account_id", error.problem) from error
