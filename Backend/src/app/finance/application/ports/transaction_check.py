from typing import Protocol

from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.entities.transaction import Transaction


class TransactionCheck(Protocol):
    async def check(
        self, transaction: Transaction, uow: UnitOfWork
    ) -> list[TransactionWarning]: ...
