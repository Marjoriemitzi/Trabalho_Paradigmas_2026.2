from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.transfers import (
    ListTransfersInput,
    TransferListOutput,
    TransferOutput,
)
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period


class ListTransfersInputPort(Protocol):
    async def execute(self, data: ListTransfersInput) -> None: ...


class ListTransfersOutputPort(Protocol):
    def present_listed(self, listing: TransferListOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...


@dataclass(frozen=True, slots=True)
class ListTransfersInteractor(ListTransfersInputPort):
    uow: UnitOfWork
    presenter: ListTransfersOutputPort

    async def execute(self, data: ListTransfersInput) -> None:
        try:
            period = Period(data.start, data.end)
        except InvalidValueError as error:
            self.presenter.present_invalid("to", error.problem)
            return

        async with self.uow:
            transfers = await self.uow.transfers.list_all_between(
                OwnerId(data.owner_id), period
            )

        self.presenter.present_listed(
            TransferListOutput(
                start=period.start.isoformat(),
                end=period.end.isoformat(),
                transfers=[TransferOutput.from_transfer(t) for t in transfers],
            )
        )
