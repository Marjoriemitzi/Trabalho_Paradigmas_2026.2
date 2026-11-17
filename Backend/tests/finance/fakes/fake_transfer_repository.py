from dataclasses import replace
from datetime import date

from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transfer_flows import TransferFlows
from app.finance.domain.value_objects.transfer_id import TransferId


class FakeTransferRepository:
    def __init__(self) -> None:
        self.stored: list[Transfer] = []

    async def add(self, transfer: Transfer) -> None:
        self.stored.append(transfer)

    async def get(self, owner: OwnerId, transfer_id: TransferId) -> Transfer | None:
        for t in self.stored:
            if t.owner == owner and t.id == transfer_id:
                return replace(t)
        return None

    async def remove(self, transfer: Transfer) -> None:
        self.stored = [t for t in self.stored if t != transfer]

    def _da_conta(self, owner: OwnerId, account: AccountId) -> list[Transfer]:
        return [t for t in self.stored if t.owner == owner and t.touches(account)]

    async def list_between(
        self, owner: OwnerId, account: AccountId, period: Period
    ) -> list[Transfer]:
        no_periodo = [
            t for t in self._da_conta(owner, account) if period.contains(t.occurred_on)
        ]
        return sorted(no_periodo, key=lambda t: t.occurred_on)

    async def flows_before(
        self, owner: OwnerId, account: AccountId, day: date
    ) -> TransferFlows:
        antes = [t for t in self._da_conta(owner, account) if t.occurred_on < day]
        return TransferFlows.of(antes, account)

    async def flows_by_account(self, owner: OwnerId) -> dict[AccountId, TransferFlows]:
        do_dono = [t for t in self.stored if t.owner == owner]
        contas = {t.source for t in do_dono} | {t.destination for t in do_dono}
        return {conta: TransferFlows.of(do_dono, conta) for conta in contas}
