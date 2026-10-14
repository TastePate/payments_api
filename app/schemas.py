from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.config import PROMO_CODES


class TariffRead(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    id: UUID
    title: str
    price: int


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tariff_id: UUID
    email: EmailStr
    method: Literal["card", "installment", "sbp"]
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None

    @field_validator("promo_code")
    @classmethod
    def check_promo_code(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if value.upper() not in PROMO_CODES:
            raise ValueError("Неизвестный промокод")

        return value.upper()


    @model_validator(mode="after")
    def check_installment_correct(self):
        if self.method == "installment" and self.installment_months is None:
            raise ValueError('Метод оплаты "installment" не может быть выбран без времени рассрочки')

        if self.method != "installment" and self.installment_months:
            raise ValueError('Нельзя указать дату рассрочки для любых способов оплаты, кроме "installment"')
        return self


class PaymentRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tariff_id: UUID
    status: Literal["pending", "succeeded", "failed", "refunded"]
    amount: int
    discount: int
    method: Literal["installment", "card", "sbp"]
    installment_months: Literal[3, 6, 12] | None
    schedule: list[int] | None
    email: EmailStr
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        # SQLite возвращает дату без tzinfo; модель сохраняет её в UTC.
        # Восстанавливаем зону, чтобы POST, GET и повторы отвечали одинаково.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class BankWebhook(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: UUID
    status: Literal["pending", "succeeded", "failed", "refunded"]
