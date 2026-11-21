from dataclasses import dataclass
from typing import Protocol, override

from app.finance.application.dtos.recurrences import DeleteRecurrenceInput
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId


class DeleteRecurrenceInputPort(Protocol):
    async def execute(self, data: DeleteRecurrenceInput) -> None: ...


class DeleteRecurrenceOutputPort(Protocol):
    def present_deleted(self) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class DeleteRecurrenceInteractor(DeleteRecurrenceInputPort):
    uow: UnitOfWork
    presenter: DeleteRecurrenceOutputPort

    @override
    async def execute(self, data: DeleteRecurrenceInput) -> None:
        async with self.uow:
            recurrence = await self.uow.recurrences.get(
                OwnerId(data.owner_id), RecurrenceId(data.recurrence_id)
            )
            if recurrence is None:
                self.presenter.present_not_found()
                return
            await self.uow.recurrences.remove(recurrence)
            await self.uow.commit()
        self.presenter.present_deleted()
