from dataclasses import dataclass
from typing import Protocol, override

from app.finance.application.dtos.transfers import CreateTransferInput, TransferOutput
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.transfer_fields import (
    read_transfer_fields,
    reference_problem,
)
from app.finance.domain.entities.transfer import Transfer
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

    @override
    async def execute(self, data: CreateTransferInput) -> None:
        try:
            campos = read_transfer_fields(
                data.from_account_id,
                data.to_account_id,
                data.amount_cents,
                data.description,
                data.occurred_on,
            )
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        owner = OwnerId(data.owner_id)
        async with self.uow:
            problema = await reference_problem(self.uow, owner, campos)
            if problema is not None:
                self.presenter.present_invalid(problema.field, problema.problem)
                return
            transfer = Transfer.record(
                owner=owner,
                source=campos.source,
                destination=campos.destination,
                amount=campos.amount,
                description=campos.description,
                occurred_on=campos.occurred_on,
            )
            await self.uow.transfers.add(transfer)
            await self.uow.commit()

        self.presenter.present_created(TransferOutput.from_transfer(transfer))
