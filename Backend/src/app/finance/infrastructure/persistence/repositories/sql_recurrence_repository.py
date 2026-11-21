from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId
from app.finance.infrastructure.persistence.mappers.recurrence_mapper import (
    to_entity,
    to_model,
)
from app.finance.infrastructure.persistence.models.recurrence_model import (
    RecurrenceModel,
)


class SqlRecurrenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, recurrence: Recurrence) -> None:
        self._session.add(to_model(recurrence))
        await self._session.flush()

    async def get(
        self, owner: OwnerId, recurrence_id: RecurrenceId
    ) -> Recurrence | None:
        consulta = select(RecurrenceModel).where(
            RecurrenceModel.id == recurrence_id.value,
            RecurrenceModel.owner_id == owner.value,
        )
        modelo = await self._session.scalar(consulta)
        return None if modelo is None else to_entity(modelo)

    async def update(self, recurrence: Recurrence) -> None:
        novo = to_model(recurrence)
        await self._session.execute(
            update(RecurrenceModel)
            .where(
                RecurrenceModel.id == recurrence.id.value,
                RecurrenceModel.owner_id == recurrence.owner.value,
            )
            .values(
                account_id=novo.account_id,
                kind=novo.kind,
                amount_cents=novo.amount_cents,
                description=novo.description,
                category=novo.category,
                frequency=novo.frequency,
                day=novo.day,
                starts_on=novo.starts_on,
                ends_on=novo.ends_on,
            )
        )
        await self._session.flush()

    async def remove(self, recurrence: Recurrence) -> None:
        await self._session.execute(
            delete(RecurrenceModel).where(
                RecurrenceModel.id == recurrence.id.value,
                RecurrenceModel.owner_id == recurrence.owner.value,
            )
        )

    async def list_by_owner(self, owner: OwnerId) -> list[Recurrence]:
        consulta = (
            select(RecurrenceModel)
            .where(RecurrenceModel.owner_id == owner.value)
            .order_by(
                RecurrenceModel.starts_on,
                func.lower(RecurrenceModel.description),
            )
        )
        return [to_entity(m) for m in await self._session.scalars(consulta)]
