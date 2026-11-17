from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.change_transaction import DeleteTransactionInput
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_id import TransactionId


class DeleteTransactionInputPort(Protocol):
    async def execute(self, data: DeleteTransactionInput) -> None: ...


class DeleteTransactionOutputPort(Protocol):
    def present_deleted(self) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class DeleteTransactionInteractor(DeleteTransactionInputPort):
    uow: UnitOfWork
    presenter: DeleteTransactionOutputPort

    async def execute(self, data: DeleteTransactionInput) -> None:
        async with self.uow:
            transaction = await self.uow.transactions.get(
                OwnerId(data.owner_id), TransactionId(data.transaction_id)
            )
            if transaction is None:
                self.presenter.present_not_found()
                return
            await self.uow.transactions.remove(transaction)
            await self.uow.commit()
        self.presenter.present_deleted()
