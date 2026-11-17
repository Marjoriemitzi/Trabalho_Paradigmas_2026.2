from sqlalchemy import Column, DateTime, Integer, String

from app.shared.infrastructure.persistence.database import Base


class AuthAttemptModel(Base):
    __tablename__ = "auth_attempts"
    key_hash = Column(String(64), primary_key=True)
    scope = Column(String(16), primary_key=True)
    window_start = Column(DateTime(timezone=True), primary_key=True)
    count = Column(Integer, nullable=False, default=1)
