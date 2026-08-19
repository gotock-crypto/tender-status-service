from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TenderStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    customer: Mapped[str] = mapped_column(String(300), nullable=False)
    contract_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    initial_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[TenderStatus] = mapped_column(
        SAEnum(TenderStatus, native_enum=False), default=TenderStatus.DRAFT, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    history: Mapped[list["TenderStatusHistory"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan", order_by="TenderStatusHistory.changed_at.desc()"
    )


class TenderStatusHistory(Base):
    __tablename__ = "tender_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status: Mapped[TenderStatus] = mapped_column(SAEnum(TenderStatus, native_enum=False), nullable=False)
    new_status: Mapped[TenderStatus] = mapped_column(SAEnum(TenderStatus, native_enum=False), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    tender: Mapped[Tender] = relationship(back_populates="history")
