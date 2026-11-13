from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.entities.transaction import Transaction


class FakeTransactionCheck:
    def __init__(self, *warnings: TransactionWarning) -> None:
        self._warnings = list(warnings)
        self.seen: list[Transaction] = []
        self.already_stored: list[bool] = []

    async def check(
        self, transaction: Transaction, uow: UnitOfWork
    ) -> list[TransactionWarning]:
        self.seen.append(transaction)
        self.already_stored.append(
            transaction in getattr(uow.transactions, "stored", [])
        )
        return list(self._warnings)
