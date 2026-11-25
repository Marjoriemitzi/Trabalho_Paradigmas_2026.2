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
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.database import Base


class RecurrenceModel(Base):
    __tablename__ = "recurrences"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        CheckConstraint("kind IN ('income', 'expense')", name="kind_known"),
        CheckConstraint("frequency IN ('monthly', 'weekly')", name="frequency_known"),
        CheckConstraint(
            "(frequency = 'monthly' AND day BETWEEN 1 AND 31)"
            " OR (frequency = 'weekly' AND day BETWEEN 1 AND 7)",
            name="day_in_range",
        ),
        CheckConstraint(
            "ends_on IS NULL OR ends_on >= starts_on", name="ends_after_start"
        ),
        Index("ix_recurrences_owner_id", "owner_id"),
        Index("ix_recurrences_owner_id_account_id", "owner_id", "account_id"),
        ForeignKeyConstraint(
            ["account_id", "owner_id"],
            ["accounts.id", "accounts.owner_id"],
            name="fk_recurrences_account_id_owner_id_accounts",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["kind", "category"],
            ["categories.kind", "categories.name"],
            name="fk_recurrences_kind_category_categories",
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
    category: Mapped[str | None] = mapped_column(String(40))
    frequency: Mapped[str] = mapped_column(String(16))
    day: Mapped[int] = mapped_column(SmallInteger)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    last_run_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
