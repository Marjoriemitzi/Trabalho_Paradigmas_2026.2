import uuid
from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.finance.application.dtos.transfers import (
    CreateTransferInput,
    TransferListOutput,
    TransferOutput,
    UpdateTransferInput,
)


class CreateTransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: StrictInt
    description: str
    occurred_on: date

    def to_input(self, owner_id: uuid.UUID) -> CreateTransferInput:
        return CreateTransferInput(
            owner_id=owner_id,
            from_account_id=self.from_account_id,
            to_account_id=self.to_account_id,
            amount_cents=self.amount_cents,
            description=self.description,
            occurred_on=self.occurred_on,
        )


class TransferResponse(BaseModel):
    id: str
    from_account_id: str
    to_account_id: str
    amount_cents: int
    description: str
    occurred_on: str

    @classmethod
    def from_output(cls, transfer: TransferOutput) -> Self:
        return cls(
            id=transfer.id,
            from_account_id=transfer.from_account_id,
            to_account_id=transfer.to_account_id,
            amount_cents=transfer.amount_cents,
            description=transfer.description,
            occurred_on=transfer.occurred_on,
        )


class UpdateTransferRequest(CreateTransferRequest):
    def to_update_input(
        self, owner_id: uuid.UUID, transfer_id: uuid.UUID
    ) -> UpdateTransferInput:
        return UpdateTransferInput(
            owner_id=owner_id,
            transfer_id=transfer_id,
            from_account_id=self.from_account_id,
            to_account_id=self.to_account_id,
            amount_cents=self.amount_cents,
            description=self.description,
            occurred_on=self.occurred_on,
        )


class TransferListResponse(BaseModel):
    start: str = Field(serialization_alias="from")
    end: str = Field(serialization_alias="to")
    transfers: list[TransferResponse]

    @classmethod
    def from_output(cls, listing: TransferListOutput) -> Self:
        return cls(
            start=listing.start,
            end=listing.end,
            transfers=[TransferResponse.from_output(t) for t in listing.transfers],
        )
