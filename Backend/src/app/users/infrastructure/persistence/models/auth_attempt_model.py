from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.database import Base


class AuthAttemptModel(Base):
    __tablename__ = "auth_attempts"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('login_pair', 'login_ip', 'register_ip')", name="scope_known"
        ),
        CheckConstraint("count > 0", name="count_positive"),
    )

    scope: Mapped[str] = mapped_column(String(16), primary_key=True)
    key_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    count: Mapped[int]
