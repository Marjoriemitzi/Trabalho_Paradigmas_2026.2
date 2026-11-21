from datetime import date
from typing import Protocol

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId


class RecurrenceRepository(Protocol):
    async def add(self, recurrence: Recurrence) -> None: ...

    async def get(
        self, owner: OwnerId, recurrence_id: RecurrenceId
    ) -> Recurrence | None: ...

    async def update(self, recurrence: Recurrence) -> None: ...

    async def remove(self, recurrence: Recurrence) -> None: ...

    async def list_by_owner(self, owner: OwnerId) -> list[Recurrence]: ...

    async def list_pending(self, today: date) -> list[Recurrence]:
        """As de todas as pessoas que ainda têm dias a lançar até `today`."""
        ...
