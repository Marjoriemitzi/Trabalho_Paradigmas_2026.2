from typing import Protocol

from app.finance.domain.entities.transaction import Transaction


class TransactionRepository(Protocol):
    async def add(self, transaction: Transaction) -> None: ...
