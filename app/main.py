from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, get_db
from app.models import Tariff
from app.schemas import TariffRead, PaymentCreate
from app.seed import seed_tariffs


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as session:
        await seed_tariffs(session)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/tariffs", response_model=list[TariffRead])
async def get_tariffs(
    session: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(Tariff)
    tariffs = await session.scalars(stmt)

    return tariffs.all()


@app.post("/payments/")
async def post_payments(
    session: Annotated[AsyncSession, Depends(get_db)],
    payment_data: PaymentCreate
):
    tariff = await session.get(Tariff, payment_data.tariff_id)

    if not tariff:
        raise HTTPException(status_code=404)






@app.get("/payments/{id}")
async def get_payment_by_id():
    pass


@app.post("/webhooks/bank")
async def post_webhook_bank():
    pass