from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.persistence.database import Base


class CategoryModel(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("kind IN ('income', 'expense')", name="kind_known"),
    )

    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    label: Mapped[str] = mapped_column(String(40))
