from dataclasses import dataclass

from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.use_cases.create_transfer import (
    CreateTransferOutputPort as UpdateTransferOutputPort,
)
from app.finance.application.use_cases.create_transfer import CreateTransferRequest
from app.finance.domain.exceptions import InvalidTransferError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_id import TransferId


@dataclass(frozen=True, slots=True)
class UpdateTransferRequest(CreateTransferRequest):
    transfer_id: str


class UpdateTransferInteractor:
    def __init__(self, uow: UnitOfWork, presenter: UpdateTransferOutputPort) -> None:
        self._uow = uow
        self._presenter = presenter

    async def execute(self, request: UpdateTransferRequest) -> None:
        try:
            owner_id = OwnerId(request.owner_id)
            transfer_id = TransferId(request.transfer_id)
            source = AccountId(request.from_account_id)
            dest = AccountId(request.to_account_id)
            amount = Money(request.amount_cents)
            desc = Description(request.description)
        except InvalidTransferError as error:
            self._presenter.present_invalid_transfer(
                [{"field": f, "problem": p} for f, p in error.problems]
            )
            return
        except ValueError:
            self._presenter.present_transfer_not_found()
            return

        transfer = await self._uow.transfers.get(owner_id, transfer_id)
        if not transfer:
            self._presenter.present_transfer_not_found()
            return

        acc_source = await self._uow.accounts.get(owner_id, source)
        acc_dest = await self._uow.accounts.get(owner_id, dest)
        if not acc_source:
            self._presenter.present_invalid_transfer(
                [{"field": "from_account_id", "problem": "not_found"}]
            )
            return
        if not acc_dest:
            self._presenter.present_invalid_transfer(
                [{"field": "to_account_id", "problem": "not_found"}]
            )
            return

        try:
            transfer.revise(source, dest, amount, desc, request.occurred_on)
        except InvalidTransferError as error:
            self._presenter.present_invalid_transfer(
                [{"field": f, "problem": p} for f, p in error.problems]
            )
            return

        await self._uow.transfers.update(transfer)
        await self._uow.commit()

        from app.finance.application.dtos.transfers import TransferResponseDto

        self._presenter.present_transfer_created(
            TransferResponseDto(
                id=transfer.id.value,
                from_account_id=source.value,
                to_account_id=dest.value,
                amount_cents=amount.cents,
                description=desc.value,
                occurred_on=transfer.occurred_on,
            )
        )
