from dataclasses import replace

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId


class FakeRecurrenceRepository:
    def __init__(self) -> None:
        self.stored: list[Recurrence] = []

    async def add(self, recurrence: Recurrence) -> None:
        self.stored.append(replace(recurrence))

    async def get(
        self, owner: OwnerId, recurrence_id: RecurrenceId
    ) -> Recurrence | None:
        guardada = next(
            (r for r in self.stored if r.owner == owner and r.id == recurrence_id),
            None,
        )
        return None if guardada is None else replace(guardada)

    async def update(self, recurrence: Recurrence) -> None:
        self.stored = [
            replace(recurrence) if r.id == recurrence.id else r for r in self.stored
        ]

    async def remove(self, recurrence: Recurrence) -> None:
        self.stored = [r for r in self.stored if r.id != recurrence.id]

    async def list_by_owner(self, owner: OwnerId) -> list[Recurrence]:
        return sorted(
            (replace(r) for r in self.stored if r.owner == owner),
            key=lambda r: (r.starts_on, r.description.text.lower()),
        )
