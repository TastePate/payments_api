from datetime import datetime, timezone

from uuid import uuid4, UUID

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tariff(Base):
    __tablename__ = "tariff"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(unique=True)
    price: Mapped[int]


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tariff_id: Mapped[UUID] = mapped_column(ForeignKey("tariff.id"))
    email: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")
    amount: Mapped[int]
    discount: Mapped[int]
    method: Mapped[str]
    installment_months: Mapped[int | None]
    schedule: Mapped[list[int] | None] = mapped_column(type_=JSON)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    idempotency_key: Mapped[str | None] = mapped_column(unique=True)
