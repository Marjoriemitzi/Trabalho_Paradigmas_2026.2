from datetime import date

from sqlalchemy import ColumnElement, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transfer_flows import TransferFlows
from app.finance.domain.value_objects.transfer_id import TransferId
from app.finance.infrastructure.persistence.mappers.transfer_mapper import (
    to_entity,
    to_model,
)
from app.finance.infrastructure.persistence.models.transfer_model import TransferModel


def _da_conta(owner: OwnerId, account: AccountId) -> list[ColumnElement[bool]]:
    return [
        TransferModel.owner_id == owner.value,
        or_(
            TransferModel.from_account_id == account.value,
            TransferModel.to_account_id == account.value,
        ),
    ]


def _soma_quando(condicao: ColumnElement[bool]) -> ColumnElement[int]:
    return func.coalesce(func.sum(TransferModel.amount_cents).filter(condicao), 0)


class SqlTransferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transfer: Transfer) -> None:
        self._session.add(to_model(transfer))
        await self._session.flush()

    async def get(self, owner: OwnerId, transfer_id: TransferId) -> Transfer | None:
        consulta = select(TransferModel).where(
            TransferModel.id == transfer_id.value,
            TransferModel.owner_id == owner.value,
        )
        modelo = await self._session.scalar(consulta)
        return None if modelo is None else to_entity(modelo)

    async def remove(self, transfer: Transfer) -> None:
        await self._session.execute(
            delete(TransferModel).where(
                TransferModel.id == transfer.id.value,
                TransferModel.owner_id == transfer.owner.value,
            )
        )

    async def list_between(
        self, owner: OwnerId, account: AccountId, period: Period
    ) -> list[Transfer]:
        consulta = (
            select(TransferModel)
            .where(
                *_da_conta(owner, account),
                TransferModel.occurred_on.between(period.start, period.end),
            )
            .order_by(TransferModel.occurred_on, TransferModel.created_at)
        )
        return [to_entity(m) for m in await self._session.scalars(consulta)]

    async def flows_before(
        self, owner: OwnerId, account: AccountId, day: date
    ) -> TransferFlows:
        consulta = select(
            _soma_quando(TransferModel.to_account_id == account.value),
            _soma_quando(TransferModel.from_account_id == account.value),
        ).where(*_da_conta(owner, account), TransferModel.occurred_on < day)
        entrou, saiu = (await self._session.execute(consulta)).one()
        return TransferFlows(incoming_cents=int(entrou), outgoing_cents=int(saiu))

    async def flows_by_account(self, owner: OwnerId) -> dict[AccountId, TransferFlows]:
        do_dono = TransferModel.owner_id == owner.value
        soma = func.sum(TransferModel.amount_cents)
        entradas = await self._session.execute(
            select(TransferModel.to_account_id, soma)
            .where(do_dono)
            .group_by(TransferModel.to_account_id)
        )
        saidas = await self._session.execute(
            select(TransferModel.from_account_id, soma)
            .where(do_dono)
            .group_by(TransferModel.from_account_id)
        )
        entrou = {conta: int(total) for conta, total in entradas}
        saiu = {conta: int(total) for conta, total in saidas}
        return {
            AccountId(conta): TransferFlows(
                incoming_cents=entrou.get(conta, 0), outgoing_cents=saiu.get(conta, 0)
            )
            for conta in entrou.keys() | saiu.keys()
        }
