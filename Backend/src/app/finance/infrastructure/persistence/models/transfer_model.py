import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.database import Base


class TransferModel(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint("from_account_id <> to_account_id", name="different_accounts"),
        Index("ix_transfers_owner_id_occurred_on", "owner_id", "occurred_on"),
        ForeignKeyConstraint(
            ["from_account_id", "owner_id"],
            ["accounts.id", "accounts.owner_id"],
            name="fk_transfers_from_account_id_owner_id_accounts",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["to_account_id", "owner_id"],
            ["accounts.id", "accounts.owner_id"],
            name="fk_transfers_to_account_id_owner_id_accounts",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    from_account_id: Mapped[uuid.UUID]
    to_account_id: Mapped[uuid.UUID]
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(String(200))
    occurred_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
