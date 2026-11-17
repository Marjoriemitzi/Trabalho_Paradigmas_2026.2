from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.exceptions import InvalidPeriodError
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period


@dataclass(frozen=True, slots=True)
class ListTransfersRequest:
    owner_id: str
    start: date
    end: date


class ListTransfersOutputPort(Protocol):
    def present_listed(self, transfers: list) -> None: ...
    def present_invalid_period(self, problems: list[dict[str, str]]) -> None: ...


class ListTransfersInteractor:
    def __init__(self, uow: UnitOfWork, presenter: ListTransfersOutputPort) -> None:
        self._uow = uow
        self._presenter = presenter

    async def execute(self, request: ListTransfersRequest) -> None:
        try:
            owner_id = OwnerId(request.owner_id)
            period = Period(request.start, request.end)
        except InvalidPeriodError as error:
            self._presenter.present_invalid_period(
                [{"field": f, "problem": p} for f, p in error.problems]
            )
            return

        transfers = await self._uow.transfers.list_all_between(owner_id, period)

        from app.finance.application.dtos.transfers import TransferResponseDto

        dto_list = [
            TransferResponseDto(
                id=t.id.value,
                from_account_id=t.source.value,
                to_account_id=t.destination.value,
                amount_cents=t.amount.cents,
                description=t.description.value,
                occurred_on=t.occurred_on,
            )
            for t in transfers
        ]
        self._presenter.present_listed(dto_list)
