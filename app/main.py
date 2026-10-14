from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi import Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.config import PROMO_CODES
from app.db import SessionLocal, get_db
from app.models import Tariff, Payment
from app.payment_calculations import create_payment_schedule
from app.schemas import TariffRead, PaymentCreate, PaymentRead, BankWebhook
from app.seed import seed_tariffs


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as session:
        await seed_tariffs(session)
    yield


app = FastAPI(lifespan=lifespan)

async def get_payment_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str
) -> Payment | None:
    stmt = select(Payment).where(Payment.idempotency_key == idempotency_key)
    return await session.scalar(stmt)


@app.get("/tariffs", response_model=list[TariffRead])
async def get_tariffs(
    session: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(Tariff)
    tariffs = await session.scalars(stmt)

    return tariffs.all()


@app.post("/payments", response_model=PaymentRead, status_code=201)
async def post_payments(
    session: Annotated[AsyncSession, Depends(get_db)],
    payment_data: PaymentCreate,
    response: Response,
    idempotency_key: Annotated[str | None, Header()] = None,
):
    current_payment: Payment | None
    if idempotency_key is not None:
        current_payment = await get_payment_by_idempotency_key(session, idempotency_key)
        if current_payment is not None:
            response.status_code = 200
            return current_payment

    tariff = await session.get(Tariff, payment_data.tariff_id)

    if not tariff:
        raise HTTPException(status_code=404)

    discount_percent = PROMO_CODES.get(payment_data.promo_code, 0)

    discount = tariff.price * discount_percent // 100
    total = tariff.price - discount
    schedule = (create_payment_schedule(total, payment_data.installment_months)
                if payment_data.method == "installment"
                else None)

    current_payment = Payment(
        tariff_id=payment_data.tariff_id,
        email=payment_data.email,
        amount=total,
        discount=discount,
        method=payment_data.method,
        installment_months=payment_data.installment_months,
        schedule=schedule,
        idempotency_key=idempotency_key
    )

    session.add(current_payment)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if idempotency_key is not None:
            current_payment = await get_payment_by_idempotency_key(session, idempotency_key)

            if current_payment is None:
                raise

            response.status_code = 200
            return current_payment
        raise

    return current_payment


@app.get("/payments/{id}", response_model=PaymentRead)
async def get_payment_by_id(
    session: Annotated[AsyncSession, Depends(get_db)],
    id: UUID
):
    payment = await session.get(Payment, id)
    if payment is None:
        raise HTTPException(status_code=404)
    return payment


@app.post("/webhooks/bank")
async def post_webhook_bank(
    session: Annotated[AsyncSession, Depends(get_db)],
    webhook_data: BankWebhook
):
    allowed_transitions = {
        "pending": ["succeeded", "failed"],
        "succeeded": ["refunded"]
    }

    payment = await session.get(Payment, webhook_data.payment_id)
    if payment is None:
        raise HTTPException(status_code=404)

    current_status = payment.status
    new_status = webhook_data.status
    if new_status not in allowed_transitions.get(current_status, []):
        return JSONResponse({"error": "invalid_transition"}, status_code=409)

    # Прежний статус проверяется в самом UPDATE: конкурентный вебхук
    # не сможет повторить переход или перезаписать результат другого запроса.
    result = await session.execute(
        update(Payment)
        .where(Payment.id == webhook_data.payment_id, Payment.status == current_status)
        .values(status=new_status)
    )
    if result.rowcount == 0:
        await session.rollback()
        return JSONResponse({"error": "invalid_transition"}, status_code=409)
    await session.commit()
    return JSONResponse({"result": "ok"})
