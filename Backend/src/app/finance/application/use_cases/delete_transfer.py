from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.transfers import DeleteTransferInput
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_id import TransferId


class DeleteTransferInputPort(Protocol):
    async def execute(self, data: DeleteTransferInput) -> None: ...


class DeleteTransferOutputPort(Protocol):
    def present_deleted(self) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class DeleteTransferInteractor(DeleteTransferInputPort):
    uow: UnitOfWork
    presenter: DeleteTransferOutputPort

    async def execute(self, data: DeleteTransferInput) -> None:
        async with self.uow:
            transfer = await self.uow.transfers.get(
                OwnerId(data.owner_id), TransferId(data.transfer_id)
            )
            if transfer is None:
                self.presenter.present_not_found()
                return
            await self.uow.transfers.remove(transfer)
            await self.uow.commit()
        self.presenter.present_deleted()
