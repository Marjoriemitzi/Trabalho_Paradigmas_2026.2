from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.transfers import TransferOutput, UpdateTransferInput
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.transfer_fields import (
    read_transfer_fields,
    reference_problem,
)
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_id import TransferId


class UpdateTransferInputPort(Protocol):
    async def execute(self, data: UpdateTransferInput) -> None: ...


class UpdateTransferOutputPort(Protocol):
    def present_updated(self, transfer: TransferOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class UpdateTransferInteractor(UpdateTransferInputPort):
    uow: UnitOfWork
    presenter: UpdateTransferOutputPort

    async def execute(self, data: UpdateTransferInput) -> None:
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
            transfer = await self.uow.transfers.get(owner, TransferId(data.transfer_id))
            if transfer is None:
                self.presenter.present_not_found()
                return
            problema = await reference_problem(self.uow, owner, campos)
            if problema is not None:
                self.presenter.present_invalid(problema.field, problema.problem)
                return
            transfer.revise(
                source=campos.source,
                destination=campos.destination,
                amount=campos.amount,
                description=campos.description,
                occurred_on=campos.occurred_on,
            )
            await self.uow.transfers.update(transfer)
            await self.uow.commit()

        self.presenter.present_updated(TransferOutput.from_transfer(transfer))
