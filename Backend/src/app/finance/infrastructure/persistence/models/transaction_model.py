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


class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint("kind IN ('income', 'expense')", name="kind_known"),
        Index("ix_transactions_owner_id_occurred_on", "owner_id", "occurred_on"),
        ForeignKeyConstraint(
            ["account_id", "owner_id"],
            ["accounts.id", "accounts.owner_id"],
            name="fk_transactions_account_id_owner_id_accounts",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["kind", "category"],
            ["categories.kind", "categories.name"],
            name="fk_transactions_kind_category_categories",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    account_id: Mapped[uuid.UUID]
    kind: Mapped[str] = mapped_column(String(16))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40))
    occurred_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
